# 01. Workflow для всех треков

## Стандартный прогон

1. Выбрать source WAV; MP3 оставить reference/codec output.
2. Проверить источники и `PluginVer/PluginBuild` current base XML.
3. Проанализировать audio: sample rate, channels, duration, LUFS/peak/crest/correlation/Side-Mid, хвост тишины.
4. Прочитать XML и декодировать `Global/ExtraBytes ElementID="ElementChain"`.
5. Если нужен stem-level correction, сделать optional `Master Rebalance` pre-stage и отдельно утвердить его.
6. Работать stage-by-stage: одна ось = один модуль.
7. Для T/S использовать подтверждённую карту v1.3. Не делать schema calibration, если build совпадает и поле уже известно.
8. Если влияние почти не слышно, сделать one-module boundary probe, затем отступить от экстремума к музыкальному winner.
9. Сравнивать с Gain Match/Delta, а затем обычным A/B на одинаковой громкости.
10. После выбора пользовательского/GUI winner назначить его новой Base XML и сохранить предыдущие модули без изменений.
11. Каждый stage рендерить из исходного source WAV, не из предыдущего обработанного WAV.
12. Maximizer делать последним.
13. Финальный WAV вывести нативно из DAW/Ozone; затем выполнить decoded MP3/AAC audit.
14. Финал фиксируется только после слухового утверждения пользователя.

## Цепь

Стандарт:

```text
Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

Optional stem-level pre-stage:

```text
Master Rebalance → Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

Master Rebalance не имеет T/S-ветки. Его SourceType/SourceGain — только GUI-verified `TRACK_DECISION`, не universal defaults.

## Drum-forward вариант

Если трек держится на ударных:

```text
Transient branch сохранять свободнее Sustain.
Impact настраивать по атаке и groove, а не по максимальной заметности ручек.
Clarity/Stabilizer/Dynamic EQ чаще сильнее работают по Sustain.
В Dynamic EQ не ловить низ kick/bass без явной проблемы.
Imager не должен ослаблять центральную атаку или важный инструмент в mono.
Maximizer останавливать до слышимой потери удара, даже если LUFS ниже цели.
```

## Когда calibration допустим

```text
PluginVer/PluginBuild изменился
появился неизвестный mode enum
нужный ParamID отсутствует в v1.3 map и Base XML
GUI противоречит подтверждённой карте
Ozone перестал сериализовать ранее подтверждённое поле
```

Новый трек сам по себе не является причиной calibration.

## Типовой stage report

```text
АКТИВНЫЙ МОДУЛЬ ЭТОГО ПРОГОНА: <module>
Base audio: <source WAV>
Base XML: <current winner>
PluginVer/Build: <...>
Что менялось: <only this module>
Provenance: <SOURCE_XML/CONFIRMED_GUI_DEFAULT/CORE_PROFILE/TRACK_DECISION>
Что НЕ трогалось: <prior accepted modules + unknown blocks>
Probe или candidate: <boundary/final-purpose>
Что рендерить: <file names>
Как слушать: <risk points including mono/codec when relevant>
```

Multi-module control pass допустим только по явной задаче и должен перечислять все изменённые модули.
