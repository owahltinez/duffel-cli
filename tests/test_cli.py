import json
from pathlib import Path

from click.testing import CliRunner

from duffel_cli import cli as cli_mod
from duffel_cli import client

FIXTURE = Path(__file__).parent / "fixtures" / "offer_request.json"


def _run(monkeypatch, args, token="duffel_test_x"):
    monkeypatch.setenv("DUFFEL_TOKEN", token)
    return CliRunner().invoke(cli_mod.cli, ["search", *args])


def test_search_passes_slices_and_prints_rows(monkeypatch):
    calls = []

    def fake_search(token, slices, *args):
        calls.append(slices)
        return json.loads(FIXTURE.read_text())["data"]["offers"]

    monkeypatch.setattr(client, "search", fake_search)
    result = _run(
        monkeypatch,
        ["--slice", "mad:syd:2026-12-26", "--slice", "SYD:MAD:2027-01-18"],
    )
    assert result.exit_code == 0, result.output
    assert calls[0][0] == {
        "origin": "MAD",
        "destination": "SYD",
        "departure_date": "2026-12-26",
    }
    rows = [json.loads(line) for line in result.output.splitlines()]
    assert len(rows) == 3


def test_search_rejects_bad_slice(monkeypatch):
    result = _run(monkeypatch, ["--slice", "MAD-SYD-2026-12-26"])
    assert result.exit_code == 2
    assert "ORIGIN:DEST:YYYY-MM-DD" in result.output


def test_search_requires_token(monkeypatch):
    result = _run(monkeypatch, ["--slice", "MAD:SYD:2026-12-26"], token="")
    assert result.exit_code == 1
    assert "DUFFEL_TOKEN" in result.output


def test_search_reports_api_errors(monkeypatch):
    def failing_search(*args):
        raise client.DuffelError("Insufficient permissions")

    monkeypatch.setattr(client, "search", failing_search)
    result = _run(monkeypatch, ["--slice", "MAD:SYD:2026-12-26"])
    assert result.exit_code == 1
    assert "Insufficient permissions" in result.output
