# CF-Check-DNS

A Python script to check the DNS entries of a given domain hosted in Cloudflare

## Usage

```
Usage: cf-check-dns [OPTIONS] [CF_ZONE]

  Print DNS records for a given Cloudflare zone.

  Usage: cf_check_dns CF_ZONE

  If no zone name is provided, a list of zones available
  to the user will be displayed.

  Credentials are accepted via the two environment variables:

  CF_API_KEY
  CF_API_EMAIL

Options:
  -V, --version  Show the version and exit.
  -h, --help     Show this message and exit.
  -v, --verbose  Repeat for extra visibility
```
