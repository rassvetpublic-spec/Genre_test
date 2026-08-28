# 03. Transient/Sustain Protocol v1.4.1

## Scope

Карта подтверждена для `PresetVer=6 / PluginVer=120002 / PluginBuild=1331`. Новый трек не требует повторной schema calibration.

```text
Transient = атака, удар, согласные, front edge.
Sustain = хвосты, reverb, ширина, long harshness и air.
```

## Confirmed map

| Модуль | Mode / selector | Transient | Sustain |
|---|---|---|---|
| Equalizer | `Processing Mode=3`, `Main/Aux Selection=1` | `Band N ...` | `Aux: Band N ...` |
| Clarity | `ProcessingMode=2` | `Amount`, `Tilt` | `Aux: Amount`, `Aux: Tilt` |
| Stabilizer | `ProcessingMode=2` | main Amount/Speed/Smoothing/Strength | corresponding `Aux:` fields |
| Stereo Imager | `Processing Mode=1`, `Transient/Sustain Selection=1` | main Width/Recover | `Aux:` Width/Recover |
| Dynamic EQ | `Processing Mode=3`, `Main/Aux Selection=1` | `Band N ...` | `Aux: Band N ...` |
| Impact | T/S channel mode не подтверждён | ordinary Impact params | Aux service fields не считать Sustain |
| Master Rebalance | T/S отсутствует | stem choice/gain | — |
| Maximizer | Main/Aux T/S отсутствует | limiter mode/linking | — |

## Equalizer

Confirmed band fields: `Enable`, `Visible`, `Frequency`, `Gain`, `Q`, `Shape`. Main = Transient; Aux = Sustain.

## Clarity

Точное имя `ProcessingMode` без пробела. `Amount/Tilt` = Transient; `Aux: Amount/Aux: Tilt` = Sustain.

## Stabilizer

Transient и Sustain имеют `Amount`, `Speed`, `FreqSmoothing`, `LFStrength`, `MFStrength`, `HFStrength`; Sustain использует соответствующие `Aux:` имена. `Target` общий.

Confirmed GUI/base point для build 1331:

```text
Amount=25
Speed=50
FreqSmoothing=50
LFStrength=100
MFStrength=100
HFStrength=100
Target=5
```

Это `CONFIRMED_GUI_DEFAULT`, если Auto XML не сериализовал поля. Накрученные calibration values default-ами не становятся. `MidSideSelection=1` считать UI state без отдельного доказательства.

## Stereo Imager

Transient/Sustain fields:

```text
Band N Width Percent
Recover Sides Enabled
Recover Sides Gain Offset (dB)
```

Sustain использует соответствующие `Aux:` имена. Common: crossovers, Module Amount, Band Active, Active Band, Stereoizer Mode. Не force-add `Enable Stereoizer`, если GUI XML его не сериализовал.

## Dynamic EQ

Подтверждены `Visible`, `Enable`, `Frequency`, `Threshold`, `Gain`, `Q`, `Shape` для main/Aux band family. Main = Transient; Aux = Sustain.

DynEQ после Imager может ловить widened long glass, но не должен broad-cut весь верх. В drum-forward профиле low bands запрещены без явно измеренной/услышанной проблемы, чтобы не ослабить kick/bass.

## Drum-forward policy

Для материала, где ударные тащат groove:

```text
Transient branch менее обработан, чем Sustain.
EQ/Clarity/Stabilizer/DynEQ чаще корректируют Sustain.
Impact сохраняет front edge и macro groove.
Imager расширяет преимущественно upper Sustain.
Maximizer не должен покупать LUFS потерей атаки.
```

Это стратегия, не набор фиксированных процентов/дБ.

## Imager safety

```text
низ/центр/primary transients держать узкими или стабильными
расширять в первую очередь upper Sustain
Stereoize/Recover Sides — только отдельным probe
Prevent Antiphase не заменяет mono audit
```

Если голос, гитара или другой важный инструмент заметно исчезает в mono, кандидат получает **HARD REJECT**. Проверять sample-aligned mono/mid, correlation и Side/Mid по полосам, затем lossy codec.


## AI alt-rock / dubstep spatial hypothesis (v1.4.1)

Для drum-forward hybrid материала сначала тестировать модель `focused transient / wider sustain`:

```text
sub + kick transient = stable/centered
snare/vocal front edge = focused
upper body/ambience/reverb/granular/vocoder sustain = progressively wider if mono survives
```

Это не фиксированные проценты. Решение принимается по A/B, Side/Mid by band, correlation, sample-aligned mono и codec audit. Если исходник уже достаточно широкий, Imager может остаться bypass.

После Imager final corrective Dynamic EQ часто логичнее перевести в M/S, чтобы отдельно ловить widened Side harshness; T/S Dynamic EQ остаётся альтернативой, если дефект доказан как transient- или sustain-specific.
