"""Flatten Duffel offers into compact rows, cheapest first."""

import re
from datetime import datetime
from itertools import pairwise

ISO_DURATION = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?")


def minutes(duration):
    """Convert an ISO 8601 duration like P1DT10H50M to minutes."""
    parsed = ISO_DURATION.fullmatch(duration)
    if not parsed:
        raise ValueError(f"unexpected duration {duration!r}")
    days, hours, mins = parsed.groups(default="0")
    return int(days) * 1440 + int(hours) * 60 + int(mins)


def hours_text(total):
    """Format minutes as 34h50m."""
    return f"{total // 60}h{total % 60:02d}m"


def _flight(segment):
    carrier = segment["marketing_carrier"]["iata_code"]
    number = segment["marketing_carrier_flight_number"].lstrip("0") or "0"
    operator = segment["operating_carrier"]["iata_code"]
    if operator != carrier:
        return f"{carrier}{number} (op. {operator})"
    return carrier + number


def _layover(arrival, departure):
    wait = datetime.fromisoformat(departure["departing_at"]) - (
        datetime.fromisoformat(arrival["arriving_at"])
    )
    airport = arrival["destination"]["iata_code"]
    if departure["origin"]["iata_code"] != airport:
        airport += ">" + departure["origin"]["iata_code"]
    return f"{airport} {hours_text(int(wait.total_seconds()) // 60)}"


def _slice(item):
    segments = item["segments"]
    route = [segments[0]["origin"]["iata_code"]]
    route += [s["destination"]["iata_code"] for s in segments]
    bags = {
        b["type"]: b["quantity"]
        for b in segments[0]["passengers"][0]["baggages"]
    }
    # Unbranded fares fall back to fare basis codes, which reveal the class
    basis = dict.fromkeys(
        s["passengers"][0]["fare_basis_code"] for s in segments
    )
    return {
        "route": "-".join(route),
        "depart": segments[0]["departing_at"][:16],
        "arrive": segments[-1]["arriving_at"][:16],
        "duration": hours_text(minutes(item["duration"])),
        "flights": [_flight(s) for s in segments],
        "layovers": [_layover(a, b) for a, b in pairwise(segments)],
        "fare": item.get("fare_brand_name") or "/".join(basis),
        "bags": bags,
    }


def summarize(offers, airlines=()):
    """Return one row per offer, cheapest and then shortest first."""
    kept = [
        o for o in offers if not airlines or o["owner"]["iata_code"] in airlines
    ]
    kept.sort(
        key=lambda o: (
            float(o["total_amount"]),
            sum(minutes(s["duration"]) for s in o["slices"]),
        )
    )
    return [
        {
            "price": float(o["total_amount"]),
            "currency": o["total_currency"],
            "airline": o["owner"]["name"],
            "slices": [_slice(s) for s in o["slices"]],
            "id": o["id"],
        }
        for o in kept
    ]
