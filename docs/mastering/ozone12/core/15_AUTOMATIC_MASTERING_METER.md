# 15. Automatic Mastering Meter

`tools/stage_toolkit/oz12_mastering_meter.py` автоматически сравнивает reference/base WAV и candidate/final WAV по трём guards:

```text
drum-attack proxy
mono-loss relative to the reference
decoded MP3/AAC peaks after real encode → decode
```

Инструмент не меняет аудио и не выбирает музыкальный winner вместо пользователя. Он создаёт воспроизводимый technical report и возвращает `FAIL` как alert.

## Requirements

```text
Python 3.10+
NumPy
SciPy
FFmpeg + ffprobe for codec audit
```

`soundfile` не требуется. Входы — PCM/float WAV.

## Quick stage check

```bash
python tools/stage_toolkit/oz12_mastering_meter.py \
  --reference "BASE.wav" \
  --candidate "CANDIDATE.wav" \
  --outdir "reports/mastering_meter" \
  --skip-codecs
```

## Final check with decoded codecs

```bash
python tools/stage_toolkit/oz12_mastering_meter.py \
  --reference "PRE_MAX_BASE.wav" \
  --candidate "NATIVE_FINAL.wav" \
  --outdir "reports/final_meter" \
  --decoded-peak-target-dbtp -1.0 \
  --keep-codec-files
```

`-1.0 dBTP` здесь только пример delivery target, а не universal default. Если `--decoded-peak-target-dbtp` не задан, peaks измеряются без PASS/FAIL по ceiling. `--keep-codec-files` сохраняет encoded и explicit float decoded файлы; без него временные codec-файлы удаляются после измерения.

## Outputs

```text
mastering_meter.json          complete machine-readable result
mastering_meter.csv           flat summary for decision log / CI
drum_attack_events.csv        event-aligned measurements
mastering_meter_report.md     human-readable decision report
codecs/                       optional encoded/decoded audit files
```

## Drum-attack proxy

1. Reference и candidate автоматически time-align по огибающей в пределах `--max-lag-seconds`.
2. Candidate получает только analysis gain для active-RMS match; аудиофайл не переписывается.
3. В reference находятся сильные broad-band onsets в полосе примерно `35–12000 Hz`.
4. На тех же событиях сравниваются attack peak, attack RMS и attack-to-sustain contrast.
5. Primary guard:

```text
attack_guard_delta = min(
  median candidate-minus-reference attack RMS,
  median candidate-minus-reference attack-to-sustain contrast
)
```

CLI defaults: warning ниже `-0.5 dB`, fail ниже `-1.0 dB`; оба порога настраиваются. Это переносимая review heuristic, не универсальный закон. Detector работает по full master и не является drum-stem separation. Для drum-forward трека слышимая потеря punch/groove остаётся stop-критерием.

## Mono loss

Для stereo overall, drum-event windows и четырёх полос считается mono retention:

```text
10*log10(
  power((L+R)/2) / ((power(L)+power(R))/2)
)
```

`0 dB` соответствует полностью coherent center; более отрицательное значение означает меньшую сохранность при mono fold-down. Decision metric — `candidate retention - reference retention`: отрицательный delta означает дополнительную потерю относительно base.

CLI defaults: warning ниже `-1 dB`, fail ниже `-3 dB`. Очень тихая полоса остаётся `MEASURED` и не управляет итогом. Без stems инструмент не идентифицируется: если гитара/вокал исчезает в mono, слуховой hard reject имеет приоритет даже при numeric PASS.

## Decoded codec peaks

По умолчанию создаются и декодируются:

```text
MP3 320 kbps
AAC 256 kbps
AAC 192 kbps stress test
```

Decoded true peak измеряется FFmpeg `ebur128=peak=true` на explicit float decoded WAV. При заданном target инструмент считает:

```text
recommended_source_trim_db = max(
  0,
  measured_decoded_TP - target_TP + safety_margin
)
```

После trim обязателен повторный encode → decode → measure. Значение одного кодека не переносится на другой.

## Exit codes and self-test

Обычный запуск возвращает `0`, если отчёт успешно создан, даже когда metric status = `FAIL`. Для CI добавить `--strict`: тогда overall `FAIL` возвращает exit code `3`.

```bash
python tools/stage_toolkit/oz12_mastering_meter.py --self-test
```

Self-test синтезирует ослабленные drum attacks и фазовую high-band потерю, затем проверяет все три codec decode paths и четыре output-файла.
