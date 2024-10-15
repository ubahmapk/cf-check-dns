# CF-Check-DNS

A Python script to check the DNS entries of a given domain hosted in Cloudflare

## Usage

```
Usage: cf-check-dns [OPTIONS]

  Print DNS records for a given Cloudflare zone.

  Credentials should be passed via the two environment variables:

  CF_API_KEY
  CF_API_EMAIL

Options:
  -V, --version        Show the version and exit.
  -h, --help           Show this message and exit.
  --cf_api_key TEXT    Cloudflare API key  [required]
  --cf_api_email TEXT  Cloudflare API email address  [required]
  -z, --zone TEXT      Cloudflare zone  [required]
  -v, --verbose        Repeat for extra visibility
```
