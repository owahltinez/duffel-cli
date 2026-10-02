# duffel-cli

Search live airline fares from the terminal via the [Duffel API](https://duffel.com/docs).
Built for AI agents: one compact JSON row per offer, cheapest first.

## Install

```sh
uv tool install duffel-cli
```

The distribution is `duffel-cli`; the command it installs is `duffel`.

## Authenticate

Create a live, read-write access token in the Duffel dashboard under
Developers → Access tokens, then export it:

```sh
export DUFFEL_TOKEN=duffel_live_...
```

Test tokens work too, but only return the fictional Duffel Airways.

## Search

Each `--slice` is one leg. Use one for one-way, two for a return, more for
multi-city trips such as stopovers:

```sh
duffel search --slice MAD:SYD:2026-12-26 --slice SYD:MAD:2027-01-18
duffel search --slice MAD:CAN:2026-12-24 --slice CAN:SYD:2026-12-27 \
  --airline CZ --max-connections 0
```

Options: `--adults`, `--cabin`, `--max-connections`, `--airline` and `--limit`.

```json
{"price": 1520.1, "currency": "USD", "airline": "China Eastern Airlines",
 "slices": [{"route": "MAD-PVG-SYD", "depart": "2026-12-26T10:30",
   "arrive": "2026-12-28T05:20", "duration": "34h50m",
   "flights": ["MU710", "MU561"], "layovers": ["PVG 13h30m"],
   "fare": "Economy Standard", "bags": {"checked": 2, "carry_on": 1}}],
 "id": "off_..."}
```

Times are local to each airport. A layover such as `LHR>LGW 4h00m` means
changing airports. Unbranded fares show their fare basis codes instead, such as
`Y2AFFYIT`; a leading `Y` usually means a full-price economy fare.

## Scope

Search only. Duffel offers can be booked through its API, but this tool leaves
booking to the airline or a travel agent.

## Development

```sh
uv sync --extra dev
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q
```
