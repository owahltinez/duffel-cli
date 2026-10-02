"""duffel: search live airline fares from the terminal."""

import json
import os
import re

import click

from duffel_cli import client, offers

CABINS = ["economy", "premium_economy", "business", "first"]
SLICE = re.compile(r"([A-Z]{3}):([A-Z]{3}):(\d{4}-\d{2}-\d{2})")


def _parse_slices(ctx, param, values):
    slices = []
    for value in values:
        parsed = SLICE.fullmatch(value.upper())
        if not parsed:
            raise click.BadParameter(f"{value!r} is not ORIGIN:DEST:YYYY-MM-DD")
        origin, destination, date = parsed.groups()
        slices.append(
            {
                "origin": origin,
                "destination": destination,
                "departure_date": date,
            }
        )
    return slices


@click.group()
def cli():
    """Search live airline fares via the Duffel API."""


@cli.command()
@click.option(
    "--slice",
    "slices",
    multiple=True,
    required=True,
    callback=_parse_slices,
    metavar="ORIGIN:DEST:DATE",
    help="One leg, e.g. MAD:SYD:2026-12-26; repeat for return or multi-city.",
)
@click.option(
    "--adults", default=1, show_default=True, type=click.IntRange(1, 9)
)
@click.option(
    "--cabin", default="economy", show_default=True, type=click.Choice(CABINS)
)
@click.option(
    "--max-connections",
    type=click.IntRange(0, 2),
    help="Maximum connections per leg.",
)
@click.option(
    "--airline",
    "airlines",
    multiple=True,
    metavar="IATA",
    help="Only offers sold by this airline, e.g. CZ; repeatable.",
)
@click.option("--limit", default=10, show_default=True, type=click.IntRange(1))
def search(slices, adults, cabin, max_connections, airlines, limit):
    """Search fares for one or more legs, one JSON row per offer."""
    token = os.environ.get("DUFFEL_TOKEN")
    if not token:
        raise click.ClickException("DUFFEL_TOKEN is not set")
    try:
        found = client.search(token, slices, adults, cabin, max_connections)
    except client.DuffelError as error:
        raise click.ClickException(str(error)) from None
    airlines = {a.upper() for a in airlines}
    for row in offers.summarize(found, airlines)[:limit]:
        click.echo(json.dumps(row, ensure_ascii=False))
