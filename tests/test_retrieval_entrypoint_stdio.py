from __future__ import annotations

import io

from genre_test.retrieval.entrypoint import _make_stream_encoding_tolerant


def test_make_stream_encoding_tolerant_prevents_cp1251_unicode_crash() -> None:
    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1251", errors="strict")

    _make_stream_encoding_tolerant(stream)

    assert stream.encoding.lower() == "cp1251"
    assert stream.errors == "backslashreplace"

    stream.write("Beyoncé / Музыка")
    stream.flush()

    rendered = raw.getvalue().decode("cp1251")
    assert rendered == r"Beyonc\xe9 / Музыка"


class _NonReconfigurableStream:
    def reconfigure(self, **_: object) -> None:
        raise ValueError("locked")


def test_make_stream_encoding_tolerant_accepts_locked_stream() -> None:
    _make_stream_encoding_tolerant(_NonReconfigurableStream())
