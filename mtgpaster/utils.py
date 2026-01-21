import requests

SCRYFALL_URL = "https://api.scryfall.com/cards/search"


def make_request(card_name: str) -> dict:
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
