import requests

SCRYFALL_URL = "https://api.scryfall.com/cards/search"
"""
Base API url for the ScyFall API.
"""

def make_request(card_name: str) -> dict:
    """
    Fuzzily searches the scryfall API for a passed card name.

    :param card_name: The card name to fuzzy search for.
    :return: Returns a data dictionary from the ScyFall API. If an error occurs, returns an empty dictionary.
    """
    response = requests.get(url=SCRYFALL_URL, params={"q": card_name})

    try:
        response.raise_for_status()
        return response.json()

    except requests.HTTPError as error:
        match error:
            case 404:
                print("ERROR: No cards matched the criteria.")
            case _:
                print("ERROR: A network error occurred. Please check your network status and try again.")

        return {}
