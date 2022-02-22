# Singer Tap for Shopify

This Shopify tap produces JSON-formatted data following the Singer spec.

[![test](https://github.com/matatika/tap-shopify/actions/workflows/ci_workflow.yml/badge.svg)](https://github.com/matatika/tap-shopify/actions/workflows/ci_workflow.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/github/license/matatika/tap-shopify)](LICENSE.md)
[![Python](https://img.shields.io/static/v1?logo=python&label=python&message=3.8%20|%203.9%20|%203.10&color=blue)]()

`tap-shopify` is a Singer tap for the [Shopify REST API](https://shopify.dev/api) built 
with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Supported Streams

* [Abandoned Checkouts](https://shopify.dev/api/admin-rest/2022-01/resources/abandoned-checkouts)
* [Collects](https://shopify.dev/api/admin-rest/2022-01/resources/collect)
* [Custom Collections](https://shopify.dev/api/admin-rest/2022-01/resources/customcollection)
* [Customers](https://shopify.dev/api/admin-rest/2022-01/resources/customer)
* [Inventory Item](https://shopify.dev/api/admin-rest/2022-01/resources/inventoryitem)
* [Inventory Levels](https://shopify.dev/api/admin-rest/2022-01/resources/inventorylevel)
* [Locations](https://shopify.dev/api/admin-rest/2022-01/resources/location)
* [Metafields](https://shopify.dev/api/admin-rest/2022-01/resources/metafield)
* [Orders](https://shopify.dev/api/admin-rest/2022-01/resources/order)
* [Products](https://shopify.dev/api/admin-rest/2022-01/resources/product)
* [Transactions](https://shopify.dev/api/admin-rest/2022-01/resources/transaction)


## Installation
Use pip to install a release from GitHub

```bash
pip install git+https://github.com/Matatika/tap-shopify@vx.x.x
```

## Configuration

### Accepted Config Options

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-shopify --about
```

### Source Authentication and Authorization

- [ ] `Developer TODO:` If your tap requires special access on the source system, or any special authentication requirements, provide those here.

## Usage

You can easily run `tap-shopify` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-shopify --version
tap-shopify --help
tap-shopify --config CONFIG --discover > ./catalog.json
```

## Developer Resources

- [ ] `Developer TODO:` As a first step, scan the entire project for the text "`TODO:`" and complete any recommended steps, deleting the "TODO" references once completed.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_shopify/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-shopify` CLI interface directly using `poetry run`:

```bash
poetry run tap-shopify --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in the file.

Next, install Meltano (if you haven't already) and any additional plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-shopify
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-shopify --version
# OR run a test `elt` pipeline:
meltano elt tap-shopify target-jsonl
```


## Cloud hosting and SaaS
Our team would be happy to help [www.matatika.com](https://www.matatika.com)


## License
[AGPLv3 License](LICENSE)

It is our intention that all subsequent changes to this software are made available to the community. Under the terms of this license, you must open source your platform code if you distribute this software-as-a-service.  Applications that reside inside an organization’s network do not trigger the release of the source code.


---

Copyright &copy; 2022 Matatika
