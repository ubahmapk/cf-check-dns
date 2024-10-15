from sys import exit, stderr

import click
import httpx
from loguru import logger

__author__ = "jm@phyxt.net"
__version__ = "0.5.0"


class ZoneNotFoundError(Exception):
    pass


def set_logging_level(verbosity: int) -> None:
    """Set the global logging level"""

    # Default level
    log_level = "INFO"

    if verbosity is not None:
        if verbosity == 1:
            log_level = "INFO"
        elif verbosity > 1:
            log_level = "DEBUG"
        else:
            log_level = "ERROR"

    logger.remove(0)
    # noinspection PyUnboundLocalVariable
    logger.add(stderr, level=log_level)

    return None


def get_zone_id(client: httpx.Client, cf_zone: str) -> str:
    """Return the CF zone ID for a given Zone name."""

    try:
        logger.debug(f"In get_zone_id: {cf_zone=}")
        result: dict = client.get("/zones").json()["result"]
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to retrieve ZoneID for {cf_zone}\nError details: {exc}") from exc

    try:
        zone_id: str = next(zone["id"] for zone in result if zone["name"] == cf_zone)
    except StopIteration:
        click.secho(f'Zone "{cf_zone}" not found', fg="red", bold=True)
        click.echo()
        exit(404)

    logger.debug(f"Returning {zone_id=}")
    return zone_id


def retrieve_dns_records(client: httpx.Client, zone_id: str) -> dict:
    """Retrieve all DNS records for a given zone."""

    try:
        logger.debug(f"In retrieve_dns_records: {zone_id=}")
        result: dict = client.get(f"/zones/{zone_id}/dns_records").json()["result"]
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to retrieve ZoneID for {zone_id}") from exc

    return result


def print_dns_records(dns_records: dict) -> None:
    """Print all DNS records for a given zone."""

    if len(dns_records) == 0:
        print("No DNS records found")
        print()
        return None

    for record in dns_records:
        print(f"Host:         {record.get('name', '')}")
        print(f"Address:      {record.get('content', '')}")
        print(f"Last Updated: {record.get('modified_on', '')}")
        print()


@click.command()
@click.version_option(__version__, "-V", "--version")
@click.help_option("-h", "--help")
@click.option("--cf_api_key", required=True, help="Cloudflare API key", envvar="CF_API_KEY")
@click.option("--cf_api_email", required=True, help="Cloudflare API email address", envvar="CF_API_EMAIL")
@click.option("-z", "--zone", "cf_zone", required=True, help="Cloudflare zone")
@click.option("-v", "--verbose", "verbosity", help="Repeat for extra visibility", count=True)
def main(cf_api_key: str, cf_api_email: str, cf_zone: str, verbosity: int) -> None:
    """
    \b
    Print DNS records for a given Cloudflare zone.

    \b
    Credentials should be passed via the two environment variables:

    \b
    CF_API_KEY
    CF_API_EMAIL
    """

    set_logging_level(verbosity)

    client_headers = {
        "X-Auth-Key": cf_api_key,
        "X-Auth-Email": cf_api_email,
        "Content-Type": "application/json",
    }

    client = httpx.Client(base_url="https://api.cloudflare.com/client/v4", headers=client_headers)

    cf_zone_id: str = ""

    with client as client:
        try:
            cf_zone_id = get_zone_id(client, cf_zone)
            logger.debug(f"{cf_zone_id=}")
        except ZoneNotFoundError:
            exit("Unable to retrieve Zone ID")

        dns_records: dict = retrieve_dns_records(client, cf_zone_id)

    print_dns_records(dns_records)
