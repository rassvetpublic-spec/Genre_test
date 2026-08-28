# 05. Maximizer Rules v1.3

## Actual control

```text
Maximizer / Gain = фактический loudness drive
Target Loudness [dB] = target/display/learn metadata
```

Изменение Target Loudness без Gain не гарантирует изменение DSP.

## Confirmed fields

```text
Mode
Margin
EnableSoftClipping
SoftClipMix
LowLevelBoostWetAmount
Prevent Intersample Clipping
EnableLowLevelBoost
Gain
Stereo Link
Stereo Transient Link Amount
Target Loudness [dB]
```

Для `PluginVer=120002 / PluginBuild=1331`: `Mode=3` подтверждён как `IRC 4 - Transient`. При смене build enum перепроверяется.

## Activation gate

Inactive Auto block может содержать Gain, Soft Clip или Low Level Boost, но не влияет на звук до появления Maximizer в `ElementChain`. При активации:

```text
Mode = GUI/schema verified
True Peak = On
Soft Clip = Off для первого кандидата
Low Level Boost = Off для первого кандидата
Gain/Margin = explicit TRACK_DECISION
```

Нельзя слепо переносить inherited risk settings.

## T/S

Maximizer не имеет Main/Aux T/S branch map. `Stereo Transient Link Amount` — limiter linking, а не Sustain branch. Partial stereo/transient linking допустим только как track-specific A/B.

## Loudness decision

Не использовать фиксированный LUFS как обязательный outcome. Проверять loudness-matched:

```text
LUFS-I / short-term
True Peak
LRA / macro crest
100 ms crest or event-aligned attack
stereo image
decoded MP3/AAC peaks
```

Если median event attack loss приближается примерно к `0.5–1.0 dB`, это warning/stop zone, а не универсальный закон. При слышимой потере удара остановиться раньше независимо от target LUFS.

## Common failure

```text
Target Loudness изменён, Gain нет
Maximizer отсутствует в ElementChain
не тот Mode
inherited Soft Clip/Low Level Boost активны
неверный Margin/True Peak
Normalize включён при экспорте
```

Исправление: проверить active chain, явно задать безопасное состояние, изменить Gain, рендерить из source WAV и выполнить matched audio + codec audit.
