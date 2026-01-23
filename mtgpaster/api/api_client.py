import requests

from mtgpaster.api.api_error import ApiError


class ApiClient:

    @staticmethod
    def fetch_bulk_data() -> dict | ApiError:
        """
        Fetches all card data from the ScryFall API. Note that this is an extremely intensive (100 Mb+) operation,
        should be used sparingly.
        :return: Dict of all Scryfall cards or an ApiError on failure.
        """

        response = requests.get(url="https://api.scryfall.com/bulk-data")

        try:
            response.raise_for_status()
            # We should probably validate that this first bulk data object is the oracle_cards bulk data object; however,
            # the bulk data API does seem to guarantee that the bulk data object array will be in the same order
            # every API call.
            bulk_data_uri = response.json()["data"][0]["download_uri"]
            response = requests.get(url=bulk_data_uri)

            try:
                response.raise_for_status()
                return response.json()
            except requests.HTTPError:
                return ApiError(message="Internal Server Error", http_code=500)

        except requests.HTTPError as error:
            match error:
                case _:
                    return ApiError(message="Unknown network error while fetching bulk data.", http_code=500)