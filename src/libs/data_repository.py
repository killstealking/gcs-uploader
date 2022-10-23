import os

import requests
from dotenv import load_dotenv

load_dotenv()


class ScryfallDataRepository:
    # Scryfall-Bulk-DataのJsonファイルとURL
    BULK_DATA_URL = os.environ.get(
        "BULK_DATA_URL", "https://api.scryfall.com/bulk-data"
    )
    JSON_FILE = "./all-card.json"

    SET_TYPES = ["token", "memorabilia"]
    BORDER_COLOR = ["silver", "gold"]
    DOUBLE_IMAGES = ["transform", "modal_dfc"]
    SERVICE_LANGUAGES = ["en", "ja"]
    SECURITY_STAMPS = ["oval", "triangle"]

    def __init__(self) -> None:
        self.__download()

    def __download(self) -> None:
        print("SET SCRYFALL JSON")
        if os.path.isfile(self.JSON_FILE):
            return
        bulk_data = requests.get(self.BULK_DATA_URL)
        bulk_json = bulk_data.json()
        all_card_json_url = None
        for bulk in bulk_json["data"]:
            if bulk["type"] == "all_cards":
                all_card_json_url = bulk["download_uri"]
        if all_card_json_url:
            response = requests.get(all_card_json_url)
            with open(self.JSON_FILE, "wb") as card_json:
                card_json.write(response.content)
        else:
            raise Exception("cant get download url")

    def distribute_card_image_type(self, card) -> str:
        if (
            "paper" in card["games"]
            and card["set_type"] not in self.SET_TYPES
            and card["border_color"] not in self.BORDER_COLOR
            and card["oversized"] is False
            and card["layout"] != "token"
            and card["lang"] in self.SERVICE_LANGUAGES
        ):
            if (
                "security_stamp" in card
                and card["security_stamp"] not in self.SECURITY_STAMPS
            ):
                print("unsup security")
                print(card["id"])
                return "unsupported"
            if card["layout"] in self.DOUBLE_IMAGES:
                return "double"
            elif card["layout"] == "meld":
                return "meld"
            elif card["layout"] in [
                "normal",
                "transform",
                "split",
                "leveler",
                "meld",
                "saga",
                "flip",
                "adventure",
            ]:
                return "normal"
            else:
                print("undefined")
                print(card["id"])
                return "undefined"
        return "unsupported"
