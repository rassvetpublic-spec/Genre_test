"""Command-line toolkit for safe Ozone 12 XML work."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .xml import (
    OzoneXmlError,
    assert_confirmed_preset,
    collect_params,
    encode_element_chain,
    get_element_chain,
    parse_xml,
    patch_existing_params,
    preset_identity,
    require_final_module,
    require_module,
    set_existing_param,
    write_xml,
)

IMAGER_TS_PRESETS: dict[str, dict[str, Any]] = {
    "safe": {
        "module_amount": 45.0,
        "transient_widths": [-15.0, 0.0, 5.0, 5.0],
        "sustain_widths": [-5.0, 12.0, 45.0, 35.0],
        "recover_transient_db": 0.0,
        "recover_sustain_db": 0.6,
        "crossovers": [165.0, 3000.0, 12000.0],
    },
    "strong": {
        "module_amount": 58.0,
        "transient_widths": [-20.0, 0.0, 8.0, 5.0],
        "sustain_widths": [-5.0, 22.0, 72.0, 52.0],
        "recover_transient_db": 0.0,
        "recover_sustain_db": 1.2,
        "crossovers": [165.70428467, 3484.03076172, 11999.37695312],
    },
    "extreme": {
        "module_amount": 68.0,
        "transient_widths": [-25.0, -5.0, 0.0, 0.0],
        "sustain_widths": [0.0, 30.0, 90.0, 70.0],
        "recover_transient_db": 0.0,
        "recover_sustain_db": 1.8,
        "crossovers": [165.70428467, 3484.03076172, 11999.37695312],
    },
}


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _identity_dict(root: Any) -> dict[str, str | None]:
    identity = preset_identity(root)
    return {
        "PresetVer": identity.preset_version,
        "PluginVer": identity.plugin_version,
        "PluginBuild": identity.plugin_build,
    }


def _cmd_inspect(args: argparse.Namespace) -> int:
    root = parse_xml(args.xml).getroot()
    payload = {
        "identity": _identity_dict(root),
        "element_chain": get_element_chain(root),
        "params": [
            {"ElementID": element_id, "ParamID": param_id, "Value": value}
            for (element_id, param_id), value in sorted(collect_params(root).items())
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cmd_encode_chain(args: argparse.Namespace) -> int:
    print(encode_element_chain(tuple(args.modules)))
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    base_tree = parse_xml(args.base_xml)
    base_root = base_tree.getroot()
    base_chain = get_element_chain(base_root)
    base_params = collect_params(base_root)

    chain_rows: list[dict[str, object]] = [
        {
            "file": args.base_xml.name,
            "role": "base",
            "PresetVer": preset_identity(base_root).preset_version,
            "PluginVer": preset_identity(base_root).plugin_version,
            "PluginBuild": preset_identity(base_root).plugin_build,
            "module_count": len(base_chain),
            "chain": " -> ".join(base_chain),
        }
    ]
    diff_rows: list[dict[str, object]] = []

    for candidate in args.xmls:
        root = parse_xml(candidate).getroot()
        chain = get_element_chain(root)
        identity = preset_identity(root)
        chain_rows.append(
            {
                "file": candidate.name,
                "role": "candidate",
                "PresetVer": identity.preset_version,
                "PluginVer": identity.plugin_version,
                "PluginBuild": identity.plugin_build,
                "module_count": len(chain),
                "chain": " -> ".join(chain),
            }
        )
        candidate_params = collect_params(root)
        for element_id, param_id in sorted(set(base_params) | set(candidate_params)):
            base_value = base_params.get((element_id, param_id))
            candidate_value = candidate_params.get((element_id, param_id))
            if base_value != candidate_value:
                diff_rows.append(
                    {
                        "candidate": candidate.name,
                        "ElementID": element_id,
                        "ParamID": param_id,
                        "base_value": base_value,
                        "candidate_value": candidate_value,
                    }
                )

    args.outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.outdir / "xml_chain.csv", chain_rows)
    _write_csv(args.outdir / "xml_param_diffs.csv", diff_rows)

    lines = [
        "# Ozone XML audit\n\n",
        f"Base XML: `{args.base_xml.name}`\n\n",
        "## ElementChain\n\n",
        "| File | Role | Build | Modules | Chain |\n",
        "|---|---|---|---:|---|\n",
    ]
    for row in chain_rows:
        build = f"{row['PluginVer']}/{row['PluginBuild']}"
        lines.append(
            f"| `{row['file']}` | {row['role']} | {build} | "
            f"{row['module_count']} | {row['chain']} |\n"
        )
    lines.extend(["\n## Param diffs\n\n", f"Changed Param rows: **{len(diff_rows)}**.\n\n"])
    lines.extend(
        [
            "## Safety notes\n\n",
            "- Active module order is read from `ElementChain`; `Enabled=1` is not proof of DSP activity.\n",
            "- Module order is part of mastering semantics and must be reviewed explicitly.\n",
            "- XML patch commands only mutate Params already present in a confirmed preset.\n",
            "- Audio consequences are validated with `genre-test-mastering-qc`, not inferred from XML alone.\n",
        ]
    )
    (args.outdir / "xml_audit.md").write_text("".join(lines), encoding="utf-8")
    print(f"OK: wrote XML audit to {args.outdir}")
    return 0


def _load_patch(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OzoneXmlError("Patch JSON root must be an object")
    result: dict[str, dict[str, Any]] = {}
    for element_id, params in payload.items():
        if not isinstance(element_id, str) or not isinstance(params, dict):
            raise OzoneXmlError("Patch JSON must map ElementID strings to Param maps")
        result[element_id] = {str(param_id): value for param_id, value in params.items()}
    return result


def _print_changes(changes: Sequence[Any]) -> None:
    for change in changes:
        print(
            f"{change.element_id}\t{change.param_id}\t"
            f"{change.old_value}\t{change.new_value}"
        )


def _cmd_patch_map(args: argparse.Namespace) -> int:
    tree = parse_xml(args.input_xml)
    root = tree.getroot()
    patch = _load_patch(args.patch)
    changes = patch_existing_params(root, patch, require_active_modules=True)
    write_xml(tree, args.output_xml)
    _print_changes(changes)
    print(f"Wrote {args.output_xml}")
    return 0


def _imager_patch(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    params: dict[str, Any] = {
        "Processing Mode": 1,
        "Transient/Sustain Selection": 1,
        "Module Amount": config["module_amount"],
        "Recover Sides Enabled": 1,
        "Recover Sides Gain Offset (dB)": config["recover_transient_db"],
        "Aux: Recover Sides Enabled": 1,
        "Aux: Recover Sides Gain Offset (dB)": config["recover_sustain_db"],
    }
    for index, value in enumerate(config["crossovers"], 1):
        params[f"Crossover Cutoff {index}"] = value
    for index, value in enumerate(config["transient_widths"], 1):
        params[f"Band {index} Width Percent"] = value
    for index, value in enumerate(config["sustain_widths"], 1):
        params[f"Aux: Band {index} Width Percent"] = value
    return {"Stereo Imager": params}


def _cmd_patch_imager(args: argparse.Namespace) -> int:
    tree = parse_xml(args.input_xml)
    root = tree.getroot()
    assert_confirmed_preset(root)
    require_module(root, "Stereo Imager")
    config = dict(IMAGER_TS_PRESETS[args.preset])
    if args.module_amount is not None:
        config["module_amount"] = args.module_amount
    if args.transient_widths is not None:
        config["transient_widths"] = args.transient_widths
    if args.sustain_widths is not None:
        config["sustain_widths"] = args.sustain_widths
    if args.recover_transient_db is not None:
        config["recover_transient_db"] = args.recover_transient_db
    if args.recover_sustain_db is not None:
        config["recover_sustain_db"] = args.recover_sustain_db
    changes = patch_existing_params(root, _imager_patch(config), require_active_modules=True)
    write_xml(tree, args.output_xml)
    _print_changes(changes)
    print(f"Wrote {args.output_xml}")
    return 0


def _cmd_patch_maximizer(args: argparse.Namespace) -> int:
    tree = parse_xml(args.input_xml)
    root = tree.getroot()
    assert_confirmed_preset(root)
    require_final_module(root, "Maximizer")

    values: dict[str, Any] = {}
    optional = {
        "Mode": args.mode,
        "Margin": args.margin,
        "Prevent Intersample Clipping": args.prevent_intersample_clipping,
        "Gain": args.gain,
        "Stereo Link": args.stereo_link,
        "Stereo Transient Link Amount": args.stereo_transient_link,
        "Target Loudness [dB]": args.target_loudness,
        "EnableLowLevelBoost": args.low_level_boost,
        "LowLevelBoostWetAmount": args.low_level_boost_amount,
        "EnableSoftClipping": args.soft_clipping,
        "SoftClipMix": args.soft_clip_mix,
    }
    values.update({key: value for key, value in optional.items() if value is not None})
    if not values:
        raise OzoneXmlError("No Maximizer settings supplied")

    changes = [set_existing_param(root, "Maximizer", key, value) for key, value in values.items()]
    write_xml(tree, args.output_xml)
    _print_changes(changes)
    print(f"Wrote {args.output_xml}")
    return 0


def _cmd_stage_pack(args: argparse.Namespace) -> int:
    stage_dir = args.root / "stages" / args.stage
    for subdir in ("presets", "renders", "reports", "input_refs"):
        (stage_dir / subdir).mkdir(parents=True, exist_ok=True)

    base_wav = args.base_wav or "PATH_TO_BASE.wav"
    base_xml = args.base_xml or "PATH_TO_BASE.xml"
    candidate_wav = stage_dir / "renders" / "CANDIDATE_A.wav"
    candidate_xml = stage_dir / "presets" / "CANDIDATE_A.xml"
    report_dir = stage_dir / "reports"
    text = f"""# {args.stage} — RUN COMMANDS

## Notes

{args.notes or 'TBD'}

## Base references

```text
base_wav = {base_wav}
base_xml = {base_xml}
```

## Render contract

```text
WAV / 48 kHz / 24-bit / Normalize Off / no FX before or after Ozone
```

## Backend-neutral render QC

```bash
genre-test-mastering-qc "{base_wav}" "{candidate_wav}" --output "{report_dir / 'mastering_qc.json'}"
```

Add `--codec mp3_320` / `--codec aac_256` only when decoded-codec validation is required.

## Ozone XML audit

```bash
genre-test-ozone-xml audit --base-xml "{base_xml}" --xmls "{candidate_xml}" --outdir "{report_dir / 'xml_audit'}"
```

The old `oz12_mastering_meter.py` and `oz12_analyze_stage.py` are intentionally not part of the active workflow; shared audio QC now belongs to `genre-test-mastering-qc`.
"""
    (stage_dir / "RUN_COMMANDS.md").write_text(text, encoding="utf-8")
    print(f"OK: created {stage_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genre-test-ozone-xml",
        description="Inspect, audit and safely patch confirmed Ozone 12 XML presets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("xml", type=Path)
    inspect_parser.set_defaults(func=_cmd_inspect)

    encode_parser = subparsers.add_parser("encode-chain")
    encode_parser.add_argument("modules", nargs="+")
    encode_parser.set_defaults(func=_cmd_encode_chain)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--base-xml", required=True, type=Path)
    audit_parser.add_argument("--xmls", nargs="+", required=True, type=Path)
    audit_parser.add_argument("--outdir", required=True, type=Path)
    audit_parser.set_defaults(func=_cmd_audit)

    patch_parser = subparsers.add_parser("patch-map")
    patch_parser.add_argument("input_xml", type=Path)
    patch_parser.add_argument("output_xml", type=Path)
    patch_parser.add_argument("--patch", required=True, type=Path)
    patch_parser.set_defaults(func=_cmd_patch_map)

    imager_parser = subparsers.add_parser("patch-imager-ts")
    imager_parser.add_argument("input_xml", type=Path)
    imager_parser.add_argument("output_xml", type=Path)
    imager_parser.add_argument("--preset", choices=sorted(IMAGER_TS_PRESETS), default="safe")
    imager_parser.add_argument("--module-amount", type=float)
    imager_parser.add_argument("--transient-widths", nargs=4, type=float)
    imager_parser.add_argument("--sustain-widths", nargs=4, type=float)
    imager_parser.add_argument("--recover-transient-db", type=float)
    imager_parser.add_argument("--recover-sustain-db", type=float)
    imager_parser.set_defaults(func=_cmd_patch_imager)

    maximizer_parser = subparsers.add_parser("patch-maximizer")
    maximizer_parser.add_argument("input_xml", type=Path)
    maximizer_parser.add_argument("output_xml", type=Path)
    maximizer_parser.add_argument("--mode", type=int)
    maximizer_parser.add_argument("--margin", type=float)
    maximizer_parser.add_argument("--prevent-intersample-clipping", type=int, choices=(0, 1))
    maximizer_parser.add_argument("--gain", type=float)
    maximizer_parser.add_argument("--stereo-link", type=float)
    maximizer_parser.add_argument("--stereo-transient-link", type=float)
    maximizer_parser.add_argument("--target-loudness", type=float)
    maximizer_parser.add_argument("--low-level-boost", type=int, choices=(0, 1))
    maximizer_parser.add_argument("--low-level-boost-amount", type=float)
    maximizer_parser.add_argument("--soft-clipping", type=int, choices=(0, 1))
    maximizer_parser.add_argument("--soft-clip-mix", type=float)
    maximizer_parser.set_defaults(func=_cmd_patch_maximizer)

    stage_parser = subparsers.add_parser("stage-pack")
    stage_parser.add_argument("--stage", required=True)
    stage_parser.add_argument("--root", required=True, type=Path)
    stage_parser.add_argument("--base-wav", default="")
    stage_parser.add_argument("--base-xml", default="")
    stage_parser.add_argument("--notes", default="")
    stage_parser.set_defaults(func=_cmd_stage_pack)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (OzoneXmlError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
