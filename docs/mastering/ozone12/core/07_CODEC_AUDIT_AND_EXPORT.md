# 07. Codec Audit and Export

## Source and final authority

Master source: WAV. Финал:

```text
WAV
48 kHz
24-bit
Normalize Off
native DAW/Ozone render
no unreported post-processing
```

Если принят 32-bit float render, нативный 24-bit export можно проверить sample/null comparison. Ожидаемый residual при корректном triangular/TPDF dither должен быть около noise floor, mean около нуля и в пределах нескольких LSB. Точный residual зависит от реализации и не является universal target.

Пост-конвертированный FFmpeg/control WAV — диагностический файл, но не замена нативному DAW/Ozone final, когда тот доступен.

## Dither

Для одного финального float→24-bit шага допустим triangular/TPDF dither. Не применять dither многократно к промежуточным стадиям.

## Codec audit

Минимум:

```text
MP3 320 kbps
AAC 256 kbps
AAC 192 kbps stress test
```

Каждый encoded file декодировать и сравнить с WAV после level/time alignment:

```text
LUFS/true peak/correlation/Side-Mid
normalized spectral deltas by band
8–12 and 12–18 kHz glass/sand
mono stability
duration, leading/trailing padding and gapless behaviour
```

## Decoded true peak

WAV ceiling не гарантирует, что decoded MP3/AAC останется ниже того же ceiling. Для платформенной доставки использовать WAV. Если пользователь распространяет lossy-файл напрямую, сделать codec-specific trim по фактическому decoded peak:

```text
attenuation_dB = max(0, measured_decoded_TP - target_TP + safety_margin)
```

После trim кодек нужно заново encode/decode и измерить. Один trim не переносить автоматически между MP3 и AAC.

## Automatic decoded-peak audit

```bash
python tools/stage_toolkit/oz12_mastering_meter.py \
  --reference "PRE_MAX_BASE.wav" \
  --candidate "NATIVE_FINAL.wav" \
  --outdir "reports/final_meter"
```

Команда реально кодирует и явно декодирует MP3 320, AAC 256 и AAC 192, затем измеряет decoded true peak FFmpeg `ebur128=peak=true`. Без `--decoded-peak-target-dbtp` результат остаётся `MEASURED`. Для declared target добавить параметр и, при необходимости, применить рассчитанный codec-specific trim; после этого повторить весь pass.

`--keep-codec-files` сохраняет encoded/decoded audio для прослушивания. По умолчанию временные codec-файлы удаляются, а JSON/CSV/Markdown metrics остаются.

## Reject signs

```text
glass/sand after level-matched decode
matte or distant vocal
important element disappears in mono
pumping kick or reduced drum attack
decoded true peak above delivery target
unexpected duration/padding or damaged tail
```


## When the mastering source itself is lossy

Если оригинального WAV нет:

1. исходный MP3/AAC хранить immutable;
2. декодировать один раз в float PCM и использовать его как единственную stage-base;
3. промежуточные рендеры делать lossless;
4. не интерпретировать codec cutoff как повод искусственно восстанавливать air;
5. финальный WAV маркировать как derived-from-lossy;
6. отдельно проверять повторный encode/decode, потому что второй lossy pass может усилить peaks, fizz и stereo damage.
