"""Safe Ozone 12 preset XML primitives.

This module owns Ozone-specific preset identity, ElementChain and Param mutation.
It intentionally does not perform audio analysis; backend-neutral render comparison
lives in :mod:`genre_test.technical.mastering_metrics`.
"""

from __future__ import annotations

import base64
import binascii
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import PLUGIN_BUILD, PLUGIN_VERSION, PRESET_VERSION


class OzoneXmlError(ValueError):
    """Raised when an Ozone XML preset violates a confirmed safety invariant."""


@dataclass(frozen=True)
class PresetIdentity:
    preset_version: str | None
    plugin_version: str | None
    plugin_build: str | None


@dataclass(frozen=True)
class ParamChange:
    element_id: str
    param_id: str
    old_value: str
    new_value: str


def parse_xml(path: str | Path) -> ET.ElementTree:
    """Parse an Ozone XML preset."""
    return ET.parse(str(path))


def preset_identity(root: ET.Element) -> PresetIdentity:
    return PresetIdentity(
        preset_version=root.get("PresetVer"),
        plugin_version=root.get("PluginVer"),
        plugin_build=root.get("PluginBuild"),
    )


def assert_confirmed_preset(root: ET.Element) -> PresetIdentity:
    """Reject presets outside the pinned XML schema/build map."""
    identity = preset_identity(root)
    expected = PresetIdentity(PRESET_VERSION, PLUGIN_VERSION, PLUGIN_BUILD)
    if identity != expected:
        raise OzoneXmlError(
            "Unsupported/unconfirmed Ozone preset identity: "
            f"PresetVer={identity.preset_version!r}, "
            f"PluginVer={identity.plugin_version!r}, "
            f"PluginBuild={identity.plugin_build!r}; "
            f"expected {expected}."
        )
    return identity


def decode_element_chain(data_b64: str) -> list[str]:
    """Decode Ozone ElementChain bytes.

    Confirmed encoding: repeated ``0x00 + uint32_le(byte_length) + UTF-8 name``.
    There is no count prefix.
    """
    try:
        raw = base64.b64decode(data_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise OzoneXmlError("ElementChain is not valid base64") from exc

    names: list[str] = []
    pos = 0
    while pos < len(raw):
        if raw[pos] != 0:
            raise OzoneXmlError(
                f"Invalid ElementChain marker at byte {pos}: expected 0x00, got 0x{raw[pos]:02x}"
            )
        pos += 1
        if pos + 4 > len(raw):
            raise OzoneXmlError("Truncated ElementChain length field")
        length = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        if pos + length > len(raw):
            raise OzoneXmlError(
                f"Truncated ElementChain module name: declared {length} bytes at offset {pos}"
            )
        try:
            name = raw[pos : pos + length].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise OzoneXmlError("ElementChain module name is not valid UTF-8") from exc
        pos += length
        if not name:
            raise OzoneXmlError("ElementChain contains an empty module name")
        names.append(name)
    return names


def encode_element_chain(names: list[str] | tuple[str, ...]) -> str:
    """Encode module names using the confirmed ElementChain wire format."""
    raw = bytearray()
    for name in names:
        if not name:
            raise OzoneXmlError("ElementChain module names must be non-empty")
        encoded = name.encode("utf-8")
        raw.append(0)
        raw.extend(struct.pack("<I", len(encoded)))
        raw.extend(encoded)
    return base64.b64encode(bytes(raw)).decode("ascii")


def _element_chain_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        node
        for node in root.iter("ExtraBytes")
        if node.get("ElementID") == "ElementChain"
    ]


def get_element_chain(root: ET.Element) -> list[str]:
    nodes = _element_chain_nodes(root)
    if len(nodes) != 1:
        raise OzoneXmlError(f"Expected exactly one ElementChain, found {len(nodes)}")
    data = nodes[0].get("Data")
    if not data:
        raise OzoneXmlError("ElementChain Data is empty")
    return decode_element_chain(data)


def require_module(root: ET.Element, module: str) -> list[str]:
    chain = get_element_chain(root)
    if module not in chain:
        raise OzoneXmlError(
            f"{module!r} is not active in ElementChain. Enabled=1 is not sufficient evidence."
        )
    return chain


def require_final_module(root: ET.Element, module: str) -> list[str]:
    chain = require_module(root, module)
    if chain[-1] != module:
        raise OzoneXmlError(
            f"{module!r} must be final for this operation; active chain is {' -> '.join(chain)}"
        )
    return chain


def collect_params(root: ET.Element) -> dict[tuple[str, str], str]:
    """Collect unique Param values keyed by ``(ElementID, ParamID)``."""
    result: dict[tuple[str, str], str] = {}
    for node in root.iter("Param"):
        element_id = node.get("ElementID") or ""
        param_id = node.get("ParamID") or ""
        if not element_id and not param_id:
            continue
        key = (element_id, param_id)
        if key in result:
            raise OzoneXmlError(f"Duplicate Param key encountered: {key!r}")
        result[key] = node.get("Value") or ""
    return result


def _param_nodes(root: ET.Element, element_id: str, param_id: str) -> list[ET.Element]:
    return [
        node
        for node in root.iter("Param")
        if node.get("ElementID") == element_id and node.get("ParamID") == param_id
    ]


def _format_like_existing(old_value: str, value: Any) -> str:
    if isinstance(value, str):
        return value
    number = float(value)
    if "," in old_value:
        return f"{number:.8f}".replace(".", ",")
    if "." in old_value:
        return f"{number:.8f}"
    if number.is_integer():
        return str(int(number))
    return f"{number:.8f}"


def set_existing_param(
    root: ET.Element,
    element_id: str,
    param_id: str,
    value: Any,
) -> ParamChange:
    """Patch exactly one existing Param; never synthesize unknown Param nodes."""
    nodes = _param_nodes(root, element_id, param_id)
    if len(nodes) != 1:
        raise OzoneXmlError(
            f"Expected exactly one existing Param ElementID={element_id!r} "
            f"ParamID={param_id!r}; found {len(nodes)}."
        )
    node = nodes[0]
    old_value = node.get("Value") or ""
    new_value = _format_like_existing(old_value, value)
    node.set("Value", new_value)
    return ParamChange(element_id, param_id, old_value, new_value)


def patch_existing_params(
    root: ET.Element,
    patch: dict[str, dict[str, Any]],
    *,
    require_active_modules: bool = True,
) -> list[ParamChange]:
    """Apply a strict ElementID -> ParamID -> value map.

    Mutations are limited to Param nodes already present in a confirmed preset.
    When ``require_active_modules`` is true, each patched ElementID must also be
    present in ElementChain.
    """
    assert_confirmed_preset(root)
    chain = get_element_chain(root)
    changes: list[ParamChange] = []
    for element_id, params in patch.items():
        if require_active_modules and element_id not in chain:
            raise OzoneXmlError(
                f"Refusing to patch inactive module {element_id!r}; active chain is "
                f"{' -> '.join(chain)}"
            )
        for param_id, value in params.items():
            changes.append(set_existing_param(root, element_id, param_id, value))
    return changes


def write_xml(tree: ET.ElementTree, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(path), encoding="utf-8", xml_declaration=True)
