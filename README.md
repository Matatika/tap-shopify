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


## Getting Started
1. Use pip to install a release from GitHub

```
pip install git+https://github.com/Matatika/tap-shopify@vx.x.x
```

2. Get your Shopify access token
3. Create your `config.json`


## Development


### Cloud hosting and SaaS
Our team would be happy to help [www.matatika.com](https://www.matatika.com)

### License
[AGPLv3 License](LICENSE)

It is our intention that all subsequent changes to this software are made available to the community. Under the terms of this license, you must open source your platform code if you distribute this software-as-a-service.  Applications that reside inside an organization’s network do not trigger the release of the source code.


---

Copyright &copy; 2022 Matatika
