from app.services.ocr import RapidOcrEngine


def test_parse_result_empty_when_none() -> None:
    engine = RapidOcrEngine()
    assert engine._parse_result(None) == []
    assert engine._parse_result([]) == []


def test_parse_result_converts_box_to_bounds() -> None:
    engine = RapidOcrEngine()

    result = engine._parse_result(
        [
            [[[20, 30], [80, 30], [80, 54], [20, 54]], "ECG", 0.97],
            [[[95, 30], [133, 30], [133, 54], [95, 54]], "86", 0.99],
        ]
    )

    assert [(w.words, w.left, w.top, w.width, w.height, w.score) for w in result] == [
        ("ECG", 20, 30, 60, 24, 0.97),
        ("86", 95, 30, 38, 24, 0.99),
    ]


def test_parse_result_skips_unparseable_box() -> None:
    engine = RapidOcrEngine()

    result = engine._parse_result(
        [
            [None, "no-box", 0.5],
            [[[20, 30], [80, 30], [80, 54], [20, 54]], "valid", 0.9],
        ]
    )

    assert len(result) == 1
    assert result[0].words == "valid"


def test_calc_duration_from_list() -> None:
    duration = RapidOcrEngine._calc_duration_ms([0.05, 0.0, 0.03], 0.0)
    assert duration == 80


def test_calc_duration_from_float() -> None:
    duration = RapidOcrEngine._calc_duration_ms(0.12, 0.0)
    assert duration == 120


def test_calc_duration_falls_back_to_wall_clock() -> None:
    from time import perf_counter

    started = perf_counter()
    duration = RapidOcrEngine._calc_duration_ms("unknown", started)
    assert 0 <= duration < 1000
