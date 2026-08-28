# 13. Confirmed XML Schema — PluginVer 120002 / Build 1331

Если XML root содержит `PresetVer=6 / PluginVer=120002 / PluginBuild=1331`, использовать:

```text
skills/OZONE12_XML_TRANSIENT_SUSTAIN_SKILL.md
tables/OZONE12_XML_TS_PARAM_MAP_v1_3.csv
tools/xml_patch/ozone12_confirmed_ts_schema_v1_3.json
```

## T/S enum summary

```text
Equalizer      Processing Mode=3
Clarity        ProcessingMode=2
Stabilizer     ProcessingMode=2
Stereo Imager  Processing Mode=1
Dynamic EQ     Processing Mode=3
Maximizer      Mode=3 = IRC 4 - Transient; not a T/S branch mode
```

## Branch summary

```text
EQ: Main Band = Transient; Aux Band = Sustain
Clarity: Amount/Tilt = Transient; Aux = Sustain
Stabilizer: main fields = Transient; Aux fields = Sustain
Imager: main Width/Recover = Transient; Aux = Sustain
Dynamic EQ: Main Band = Transient; Aux Band = Sustain
Impact: Aux does not mean Sustain
Master Rebalance: no T/S branch; SourceType/Gain are track decisions
Maximizer: no Main/Aux T/S branch map
```

Stabilizer confirmed GUI base: Amount 25, Speed 50, Smoothing 50, Low/Mid/High 100, Target 5. Это schema/default evidence, не musical winner.

## Revalidation trigger

Перепроверять только если build/version изменён, нужен unknown ParamID/enum, сериализация изменилась или GUI противоречит карте.
