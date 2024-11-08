from sys import exit, stderr

import click
import httpx
import pandas as pd
from loguru import logger
from pydantic import EmailStr, Field, ValidationError
from pydantic_settings import BaseSettings

from cf_check_dns.__version__ import __version__

__author__ = "ubahmapk@gmail.com"


class ZoneNotFoundError(Exception):
    pass


class Settings(BaseSettings):
    cf_api_key: str = Field(pattern=r"^[a-zA-Z0-9_]*$")
    cf_api_email: EmailStr


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


def retrieve_cf_credentials() -> tuple[str, str]:
    """Retrieve Cloudflare API credentials from environment variables"""

    cf_api_key: str = ""
    cf_api_email: str = ""

    try:
        settings = Settings()
        cf_api_key = settings.cf_api_key
        cf_api_email = settings.cf_api_email

    except ValidationError:
        message: str = "CloudFlare credentials are not set or are invalid.\n"
        message += "Please set the CF_API_KEY and CF_API_EMAIL environment variables."
        click.secho(message, fg="red", bold=True)
        exit(500)

    logger.debug("AWS credentials found in environment")

    return cf_api_key, cf_api_email


def list_cf_zones(client: httpx.Client, cf_api_email: str) -> None:
    """List all zones available to the user."""

    try:
        result: dict = client.get("/zones").json()["result"]
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to retrieve ZoneID") from exc

    print(f"Available Zones for Cloudflare user {cf_api_email}:")
    for zone in result:
        print(f"\tZone: {zone['name']}")

    return None


def get_zone_id(client: httpx.Client, cf_zone: str) -> str:
    """Return the CF zone ID for a given Zone name."""

    zone_id: str = ""

    try:
        logger.debug(f"In get_zone_id: {cf_zone=}")
        result: dict = client.get("/zones").json()["result"]
    except httpx.HTTPError as exc:
        raise ZoneNotFoundError(f"Unable to retrieve ZoneID for {cf_zone}\nError details: {exc}") from exc

    try:
        zone_id = next(zone["id"] for zone in result if zone["name"] == cf_zone)
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

    # Print the DNS records in a tabular format
    df: pd.DataFrame = pd.DataFrame.from_dict(dns_records)
    column_names: list[str] = ["modified_on", "name", "content"]
    column_headers: list[str] = ["Last Updated", "Host", "Address"]
    print(df[column_names].to_string(index=False, header=column_headers, justify="right"))

    return None


def process_single_zone(cf_zone: str, client: httpx.Client) -> None:
    """Given a zone name, print all DNS records for that zone."""

    cf_zone_id: str = ""
    dns_records: dict = {}

    with client as client:
        try:
            cf_zone_id = get_zone_id(client, cf_zone)
            logger.debug(f"{cf_zone_id=}")
        except ZoneNotFoundError:
            exit("Unable to retrieve Zone ID")

        dns_records = retrieve_dns_records(client, cf_zone_id)

    print_dns_records(dns_records)

    return None


@click.command()
@click.version_option(__version__, "-V", "--version")
@click.help_option("-h", "--help")
@click.argument("cf_zone", type=str, default="")
@click.option("-v", "--verbose", "verbosity", help="Repeat for extra visibility", count=True)
def main(cf_zone: str, verbosity: int) -> None:
    """
    \b
    Print DNS records for a given Cloudflare zone.

    Usage: cf_check_dns <zone_name>

    If no zone name is provided, a list of zones available to the user will be displayed.

    \b
    Credentials are accepted via the two environment variables:

    \b
    CF_API_KEY
    CF_API_EMAIL
    """

    set_logging_level(verbosity)

    cf_api_key, cf_api_email = retrieve_cf_credentials()

    client_headers = {
        "X-Auth-Key": cf_api_key,
        "X-Auth-Email": cf_api_email,
        "Content-Type": "application/json",
    }

    client = httpx.Client(base_url="https://api.cloudflare.com/client/v4", headers=client_headers)

    if not cf_zone:
        list_cf_zones(client, cf_api_email)
        exit()

    process_single_zone(cf_zone, client)
