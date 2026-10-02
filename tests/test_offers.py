import json
from pathlib import Path

import pytest

from duffel_cli import offers

FIXTURE = Path(__file__).parent / "fixtures" / "offer_request.json"


@pytest.fixture
def found():
    return json.loads(FIXTURE.read_text())["data"]["offers"]


@pytest.mark.parametrize(
    "duration, expected",
    [("PT12H50M", 770), ("P1DT10H50M", 2090), ("PT45M", 45), ("P1D", 1440)],
)
def test_minutes(duration, expected):
    assert offers.minutes(duration) == expected


def test_summarize_sorts_cheapest_first(found):
    rows = offers.summarize(found)
    assert [r["price"] for r in rows] == sorted(r["price"] for r in rows)
    assert rows[0]["airline"] == "China Eastern Airlines"


def test_summarize_filters_airlines(found):
    rows = offers.summarize(found, {"EY"})
    assert [r["airline"] for r in rows] == ["Etihad Airways"]


def test_summarize_flattens_slice(found):
    outbound = offers.summarize(found)[0]["slices"][0]
    assert outbound["route"] == "MAD-PVG-SYD"
    assert outbound["depart"] == "2026-12-26T10:30"
    assert outbound["duration"] == "34h50m"
    assert outbound["flights"][0] == "MU710"
    assert outbound["layovers"][0].startswith("PVG ")
    assert outbound["bags"] == {"checked": 2, "carry_on": 1}


def test_layover_flags_airport_change(found):
    segments = found[0]["slices"][0]["segments"]
    segments[1]["origin"] = {**segments[1]["origin"], "iata_code": "XXX"}
    layover = offers.summarize(found[:1])[0]["slices"][0]["layovers"][0]
    assert ">XXX " in layover
