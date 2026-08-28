# 02. XML Rulebook

## ElementChain — единственная активная цепь

Активную видимую цепь читать через:

```text
Global / ExtraBytes ElementID="ElementChain"
```

`Enabled=1` и сохранённый module block не доказывают, что модуль участвует в DSP.

Наблюдённое кодирование каждого имени:

```text
0x00 + uint32 little-endian byte length + UTF-8 module name
```

После изменения chain обязательно decode-back audit точного порядка.

## Стандартная и optional цепь

```text
Equalizer → Impact → Clarity → Stabilizer → Stereo Imager → Dynamic EQ → Maximizer
```

`Master Rebalance` допустим только как optional pre-stage перед Equalizer. Его наличие подтверждается `ElementChain`. Наблюдённые `SourceType`/`SourceGain` требуют GUI-проверки и `TRACK_DECISION`; универсальные enum/gain defaults запрещены.

## Base/winner precedence

Current base определяется последним явно принятым XML. Если пользователь сохранил ручную GUI-версию и выбрал её, следующий patch строится от неё. Все ранее принятые module blocks, unknown nodes, GUID/host/cache и `ExtraBytes` сохраняются без изменений вне заявленного scope.

## Float и provenance

Для подтверждённой версии float обычно сериализуется с десятичной запятой:

```text
25,00000000
-1,00002098
```

Каждое новое значение получает роль:

```text
SOURCE_XML
CONFIRMED_GUI_DEFAULT
CORE_PROFILE
TRACK_DECISION
CALIBRATION_ONLY
```

`CALIBRATION_ONLY` нельзя переносить в рабочий XML как musical/default value.

## Patch rules

```text
менять только известные параметры
не менять структуру и unknown data без необходимости
не создавать ParamID ради симметрии, если он не подтверждён
для build 1331 использовать tables/OZONE12_XML_TS_PARAM_MAP_v1_3.csv
после патча: parse + duplicate ParamID + ElementChain + intended-scope diff
```

`Aux:` трактуется только по карте модуля. В EQ/Clarity/Stabilizer/Imager/Dynamic EQ подтверждённые Aux-поля образуют Sustain. В Impact `Aux: Envelope` и `Aux: HostSyncEnvelopeEnabled` не являются Sustain branch.

## Inactive blocks

Параметры inactive module block не слышны, пока модуль отсутствует в `ElementChain`. При активации нельзя слепо наследовать опасные Auto-настройки: Soft Clip, Low Level Boost, Stereoize и другие risk fields нужно явно проверить и при отсутствии отдельного теста нейтрализовать.

## Invalid preset

Вернуться к последнему XML, который точно грузился, и применить минимальный diff. Проверить `ElementChain`, служебные узлы, unknown blocks, формат float и неподтверждённые ParamID.

## Stage artifacts

Минимум:

```text
xml_diff.csv
stage_report.md
```

Diff обязан подтверждать, что изменён только активный модуль или явно объявленный control pass.
