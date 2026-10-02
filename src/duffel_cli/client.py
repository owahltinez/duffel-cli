"""Minimal client for the Duffel offer requests endpoint."""

import json
import urllib.error
import urllib.request

API_URL = "https://api.duffel.com/air/offer_requests"
# Airlines answer at different speeds; wait for the slow ones up to this long.
SUPPLIER_TIMEOUT_MS = 60_000


class DuffelError(Exception):
    """The Duffel API rejected the request."""


def search(token, slices, adults=1, cabin="economy", max_connections=None):
    """Create an offer request and return its offers."""
    data = {
        "slices": slices,
        "passengers": [{"type": "adult"} for _ in range(adults)],
        "cabin_class": cabin,
    }
    if max_connections is not None:
        data["max_connections"] = max_connections

    query = f"return_offers=true&supplier_timeout={SUPPLIER_TIMEOUT_MS}"
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        data=json.dumps({"data": data}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Duffel-Version": "v2",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)["data"]["offers"]
    except urllib.error.HTTPError as error:
        try:
            errors = json.load(error)["errors"]
        except (ValueError, KeyError):
            errors = [{"message": str(error)}]
        raise DuffelError("; ".join(e["message"] for e in errors)) from None
