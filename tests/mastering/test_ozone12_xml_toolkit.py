from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from genre_test.mastering.ozone12.xml import (
    OzoneXmlError,
    assert_confirmed_preset,
    decode_element_chain,
    encode_element_chain,
    get_element_chain,
    patch_existing_params,
    require_final_module,
)
from genre_test.mastering.ozone12.xml_cli import main


def _preset_xml(chain: list[str]) -> str:
    encoded = encode_element_chain(chain)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<Ozone PresetVer="6" PluginVer="120002" PluginBuild="1331">
  <Imager>
    <Param ElementID="Stereo Imager" ParamID="Processing Mode" Value="0" />
    <Param ElementID="Stereo Imager" ParamID="Module Amount" Value="10,00000000" />
  </Imager>
  <Maximizer>
    <Param ElementID="Maximizer" ParamID="Mode" Value="3" />
    <Param ElementID="Maximizer" ParamID="Margin" Value="-1,00000000" />
    <Param ElementID="Maximizer" ParamID="Gain" Value="1,00000000" />
    <Param ElementID="Maximizer" ParamID="Prevent Intersample Clipping" Value="1" />
  </Maximizer>
  <Global>
    <ExtraBytes ElementID="ElementChain" Data="{encoded}" />
  </Global>
</Ozone>
"""


def _write_preset(path: Path, chain: list[str]) -> None:
    path.write_text(_preset_xml(chain), encoding="utf-8")


def test_element_chain_round_trip_preserves_order() -> None:
    chain = ["Equalizer", "Impact", "Stereo Imager", "Dynamic EQ", "Maximizer"]
    encoded = encode_element_chain(chain)
    assert decode_element_chain(encoded) == chain


def test_confirmed_identity_and_chain_are_read_from_xml() -> None:
    root = ET.fromstring(_preset_xml(["Stereo Imager", "Maximizer"]))
    identity = assert_confirmed_preset(root)
    assert identity.plugin_version == "120002"
    assert identity.plugin_build == "1331"
    assert get_element_chain(root) == ["Stereo Imager", "Maximizer"]


def test_unconfirmed_build_is_rejected_before_mutation() -> None:
    root = ET.fromstring(
        _preset_xml(["Stereo Imager", "Maximizer"]).replace(
            'PluginBuild="1331"', 'PluginBuild="9999"'
        )
    )
    with pytest.raises(OzoneXmlError, match="Unsupported/unconfirmed"):
        patch_existing_params(root, {"Maximizer": {"Gain": 2.0}})


def test_patch_is_strict_existing_only_and_preserves_comma_decimal() -> None:
    root = ET.fromstring(_preset_xml(["Stereo Imager", "Maximizer"]))
    changes = patch_existing_params(root, {"Maximizer": {"Gain": 2.75}})
    assert changes[0].old_value == "1,00000000"
    assert changes[0].new_value == "2,75000000"

    with pytest.raises(OzoneXmlError, match="found 0"):
        patch_existing_params(root, {"Maximizer": {"Unconfirmed Param": 1}})


def test_patch_rejects_module_not_active_in_element_chain() -> None:
    root = ET.fromstring(_preset_xml(["Maximizer"]))
    with pytest.raises(OzoneXmlError, match="inactive module"):
        patch_existing_params(root, {"Stereo Imager": {"Module Amount": 50}})


def test_maximizer_operation_requires_maximizer_to_be_final() -> None:
    root = ET.fromstring(_preset_xml(["Maximizer", "Stereo Imager"]))
    with pytest.raises(OzoneXmlError, match="must be final"):
        require_final_module(root, "Maximizer")


def test_cli_patch_map_uses_safe_core(tmp_path: Path) -> None:
    source = tmp_path / "source.xml"
    output = tmp_path / "patched.xml"
    patch = tmp_path / "patch.json"
    _write_preset(source, ["Stereo Imager", "Maximizer"])
    patch.write_text(json.dumps({"Maximizer": {"Gain": 2.5}}), encoding="utf-8")

    assert main(["patch-map", str(source), str(output), "--patch", str(patch)]) == 0
    root = ET.parse(output).getroot()
    gain = next(
        node
        for node in root.iter("Param")
        if node.get("ElementID") == "Maximizer" and node.get("ParamID") == "Gain"
    )
    assert gain.get("Value") == "2,50000000"


def test_cli_maximizer_refuses_nonfinal_chain(tmp_path: Path) -> None:
    source = tmp_path / "source.xml"
    output = tmp_path / "patched.xml"
    _write_preset(source, ["Maximizer", "Stereo Imager"])

    assert (
        main(["patch-maximizer", str(source), str(output), "--gain", "2.5"])
        == 2
    )
    assert not output.exists()


def test_stage_pack_routes_audio_analysis_to_shared_mastering_qc(tmp_path: Path) -> None:
    assert (
        main(
            [
                "stage-pack",
                "--stage",
                "test_stage",
                "--root",
                str(tmp_path),
                "--base-wav",
                "SOURCE.wav",
                "--base-xml",
                "BASE.xml",
            ]
        )
        == 0
    )
    text = (tmp_path / "stages" / "test_stage" / "RUN_COMMANDS.md").read_text(
        encoding="utf-8"
    )
    assert "genre-test-mastering-qc" in text
    assert "genre-test-ozone-xml audit" in text
    assert "old `oz12_mastering_meter.py`" in text
