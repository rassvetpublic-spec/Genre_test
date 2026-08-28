from genre_test.mastering.ozone12 import (
    KNOWLEDGE_REVISION,
    PLUGIN_BUILD,
    PLUGIN_VERSION,
    PRESET_VERSION,
)


def test_ozone12_confirmed_identity() -> None:
    assert PRESET_VERSION == "6"
    assert PLUGIN_VERSION == "120002"
    assert PLUGIN_BUILD == "1331"
    assert KNOWLEDGE_REVISION == "1.4.1"
