# OZONE12 XML / T-S / Stage Finalization Skill v1.3

## Назначение

Reusable workflow для iZotope Ozone 12 Advanced: безопасно строить stage XML, использовать подтверждённую Transient/Sustain schema и доводить мастер до native WAV + decoded codec audit. Это не preset конкретного трека.

## Когда применять

Применять при создании/исправлении Ozone 12 XML, T/S stage-chain, drum-forward мастеринге, headphone-width с mono guard, активации Maximizer, native final export и decoded MP3/AAC audit.

## Trigger phrases

```text
Ozone 12 XML
Transient/Sustain
tr/sus
следующий stage
песня от ударных
сделай шире / wow в наушниках
проверь mono
делай Maximizer
сравни финал WAV/MP3/AAC
```

## Confirmed build

```text
PresetVer=6
PluginVer=120002
PluginBuild=1331
```

При другом build перепроверяются unknown/enum-dependent fields; известная карта не переносится слепо.

## Source gate

```text
Mastering source = WAV
MP3 = reference or codec output
Base XML = current source/auto/GUI winner
Active chain = decoded ElementChain
Active module = exactly one unless control pass declared
Changed only = declared scope
```

Если пользователь выбирает GUI-saved XML, он становится новой Base XML. Не восстанавливать прежние модули из более старого generated candidate.

## Provenance

```text
SOURCE_XML
CONFIRMED_GUI_DEFAULT
CORE_PROFILE
TRACK_DECISION
CALIBRATION_ONLY
```

`CALIBRATION_ONLY` не становится musical/default value.

## ElementChain

Стандарт:

```text
Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

Optional pre-stage:

```text
Master Rebalance → Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

Binary item: `0x00 + uint32 little-endian byte length + UTF-8 module name`. После изменения — decode-back audit. `Enabled=1` не заменяет chain.

## Master Rebalance

Нет T/S branch. Наблюдённые `SourceType` и `SourceGain` требуют GUI verification. Stem и gain — только `TRACK_DECISION`, без universal enum/amount default. Модуль влияет на DSP только если присутствует в `ElementChain`.

## Equalizer

```text
Processing Mode=3
Main/Aux Selection=1
Band N fields=Transient
Aux: Band N fields=Sustain
```

Confirmed fields: `Enable`, `Visible`, `Frequency`, `Gain`, `Q`, `Shape`.

## Clarity

```text
ProcessingMode=2
Amount/Tilt=Transient
Aux: Amount/Aux: Tilt=Sustain
```

`ProcessingMode` пишется без пробела.

## Stabilizer

`ProcessingMode=2`. Main и Aux branches имеют `Amount`, `Speed`, `FreqSmoothing`, `LFStrength`, `MFStrength`, `HFStrength`; `Target` общий.

Confirmed GUI/base point for build 1331:

```text
Amount=25; Speed=50; FreqSmoothing=50
LFStrength=100; MFStrength=100; HFStrength=100; Target=5
```

Использовать как `CONFIRMED_GUI_DEFAULT` только для отсутствующих schema fields. Calibration probe values не переносить. `MidSideSelection=1` — UI state без отдельного доказательства.

## Stereo Imager

```text
Processing Mode=1
Transient/Sustain Selection=1
main Width/Recover=Transient
Aux Width/Recover=Sustain
```

Common: crossovers, Module Amount, Band Active, Active Band, Stereoizer Mode. Не force-add `Enable Stereoizer`.

Width policy: low/center/primary transients stable; widen mainly upper Sustain. Stereoize/strong Recover Sides only as boundary probe. `Prevent Antiphase` не заменяет mono audit. Если важный instrument/vocal noticeably disappears in mono — **HARD REJECT**.

## Dynamic EQ

```text
Processing Mode=3
Main/Aux Selection=1
Band N=Transient
Aux: Band N=Sustain
```

Confirmed fields: `Visible`, `Enable`, `Frequency`, `Threshold`, `Gain`, `Q`, `Shape`. Prefer existing band numbers. После Imager можно контролировать widened long glass. В drum-forward profile low bands по kick/bass не создавать без explicit problem.

## Impact

No confirmed T/S channel mode. Ordinary fields include Global/Band Amount, Envelope, crossovers and Auto Gain. `Aux: Envelope` / `Aux: HostSyncEnvelopeEnabled` are not Sustain.

## Maximizer

No Main/Aux T/S branch. For build 1331: `Mode=3 → IRC 4 - Transient`.

Activation gate:

```text
Maximizer is present in ElementChain
Mode verified
Gain is explicit actual drive
Margin and True Peak verified
Soft Clip Off for first candidate
Low Level Boost Off for first candidate
linking preserved or separately tested
```

`Target Loudness` is not a substitute for `Gain`. Inactive Auto values become relevant only after activation and must not be inherited blindly.

## Audibility protocol

If stage is almost inaudible:

1. Verify active chain, DSP ParamID, render source and Gain Match/Delta.
2. Make one extreme boundary probe in the current module only.
3. Confirm direction.
4. Retreat to the minimum musical winner.
5. Never increase several modules together to make a difference audible.

## Drum-forward protocol

```text
Protect Transient more than Sustain.
Let EQ/Clarity/Stabilizer/DynEQ work more on Sustain when justified.
Judge Impact by punch/groove.
Do not process low DynEQ bands without a kick/bass problem.
Stop limiter drive before audible attack loss.
```

Matched event attack loss around `0.5–1.0 dB` is a warning heuristic, not an absolute law. Audible loss of punch is the stop condition.

## Automatic mastering meter

Для repeatable stage/final evidence использовать:

```text
Universal Core: tools/stage_toolkit/oz12_mastering_meter.py
rules-hub mirror: scripts/ozone12_mastering_meter.py
```

Meter автоматически:

1. time-aligns reference/candidate по reduced-rate envelope;
2. делает analysis-only active-RMS match;
3. сравнивает одни и те же strong broad-band onset events;
4. считает relative mono retention overall, вокруг drum events и по четырём полосам;
5. при final pass реально encode→decode MP3 320, AAC 256 и AAC 192 и измеряет decoded peaks.

Primary drum guard = minimum of median attack-RMS delta and median attack-to-sustain delta. Default warning/fail thresholds настраиваются и остаются heuristics. Detector не является drum-stem separation.

Mono guard использует candidate-minus-reference retention. Отрицательный delta означает дополнительную mono loss. Numeric PASS не отменяет mono listening и hard reject при исчезновении важного инструмента.

Codec delivery target не выдумывается: без `--decoded-peak-target-dbtp` peaks имеют status `MEASURED`. После codec-specific trim обязателен повторный pass.

## Workflow

1. Check root build and decode ElementChain.
2. Select current winner/base and one active module.
3. Patch only confirmed fields; preserve unknown data and prior accepted modules.
4. Parse XML; check duplicate ParamID; decode ElementChain again.
5. Diff must show intended scope only.
6. Render from source WAV.
7. Compare loudness-matched and choose winner/fallback.
8. For Imager: mono + correlation + Side/Mid by band.
9. For Maximizer/final: запустить automatic meter для event attack + mono loss + decoded codec peaks; LRA/crest оставить в stage report.

## Что менять

- Только active module или явно объявленный control pass.
- Подтверждённые mode/selector/Main/Aux/common fields с provenance.
- `ElementChain` только для осознанного добавления/порядка stage.
- Track values только как `TRACK_DECISION`.

## Что не менять

- Prior accepted module blocks вне scope.
- Unknown `ExtraBytes`, GUID/host/cache и MatchEQ snapshot без причины.
- Inactive blocks ради симметрии.
- Calibration-only или exact previous-track winner values как defaults.

## Запреты

- Не считать `Enabled=1` активной цепью и любой `Aux:` Sustain.
- Не каскадировать следующий stage из предыдущего processed WAV.
- Не усиливать несколько модулей одновременно, чтобы «услышать разницу».
- Не принимать stereo wow при заметной mono-потере важного элемента.
- Не считать `Target Loudness` фактическим Maximizer drive.
- Не считать WAV true peak гарантией decoded codec peak.

## Проверка результата

```text
XML parse/build/duplicate ParamID = PASS
ElementChain decode-back = expected
diff scope = intended module only
calibration-only contamination = none
loudness-matched musical A/B = accepted
mono/correlation/Side-Mid = accepted when width changes
attack/LRA/crest = accepted when dynamics or limiting changes
decoded codec peak/spectrum/padding = accepted for final
```

## Native final and codecs

Final authority: native DAW/Ozone 48 kHz / 24-bit WAV, Normalize Off. If an accepted float render exists, compare sample-aligned; correct dither appears as low-level unbiased residual. A post-converted control WAV is diagnostic, not a replacement for native final.

WAV true peak does not guarantee decoded MP3/AAC true peak. For direct lossy delivery:

```text
attenuation_dB = max(0, measured_decoded_TP - target_TP + safety_margin)
```

Re-encode/decode after trim. Audit MP3 320, AAC 256 and AAC 192 including spectral delta, mono, Side/Mid, correlation, duration/padding and tail.

## Calibration required only when

```text
PluginVer/Build changed
unknown enum or ParamID is required
known field stops serializing
GUI contradicts the confirmed map
```

New track ≠ calibration reason.

## Отчёт

```text
Base audio / Base XML / PluginVer-Build
Active chain / Active module / Changed only
Provenance / Probe-or-candidate
XML audit / Audio comparison / Mono-codec checks
Winner / Fallback / Reject reason / Next stage
```
