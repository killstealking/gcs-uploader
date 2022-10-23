import json
import os

import ijson
import requests
from dotenv import load_dotenv

from src.libs.gcs_setting import get_gcs_client
from src.libs.data_repository import ScryfallDataRepository

load_dotenv()


class ImageUploader:
    BUCKET_NAME = os.environ.get("BUCKET_NAME", "mtg-card-image")

    def __init__(self) -> None:
        self.data_repo = ScryfallDataRepository()
        self.gcs_client = get_gcs_client()
        self.bucket = self.gcs_client.get_bucket(self.BUCKET_NAME)

    def __create_gcs_path(
        self,
        language: str,
        expansion: str,
        collector_num: str,
        card_name: str,
        is_sub: bool = False,
    ) -> str:
        if is_sub:
            return f"/{expansion}/{language}/{card_name}_{collector_num}_sub.jpg"
        else:
            return f"/{expansion}/{language}/{card_name}_{collector_num}.jpg"

    def __download_image_to_local(self, image_url: str, image_path: str) -> None:
        image_data = requests.get(image_url).content
        with open(image_path, "wb") as card_image:
            card_image.write(image_data)

    def __delete_local_image(self, image_path: str) -> None:
        os.remove(image_path)

    def __upload_image(self, gcs_path: str, local_image_path: str) -> None:
        gcs_bucket_client = self.bucket
        blob_gcs = gcs_bucket_client.blob(gcs_path)
        blob_gcs.upload_from_filename(local_image_path)

    def __upload_normal_image(self, card):
        image_url = card["image_uris"]["large"]
        card_name = card["name"].replace("//", "__")
        expansion = card["set"]
        language = card["lang"]
        collector_number = card["collector_number"]
        gcs_path = self.__create_gcs_path(
            language=language,
            expansion=expansion,
            collector_num=collector_number,
            card_name=card_name,
            is_sub=False,
        )
        print(card_name)
        image_path = "{}.jpg".format(card_name)
        self.__download_image_to_local(image_url=image_url, image_path=image_path)
        self.__upload_image(gcs_path=gcs_path, local_image_path=image_path)
        self.__delete_local_image(image_path=image_path)

    def __upload_double_image(self, card):
        j = 1
        for card_face in card["card_faces"]:
            is_sub = True if j != 1 else False
            image_url = card_face["image_uris"]["large"]
            card_name = card_face["name"].replace("//", "__")
            expansion = card["set"]
            language = card["lang"]
            collector_number = card["collector_number"]
            gcs_path = self.__create_gcs_path(
                language=language,
                expansion=expansion,
                collector_num=collector_number,
                card_name=card_name,
                is_sub=is_sub,
            )
            print(card_name)
            image_path = "{}.jpg".format(card_name)
            self.__download_image_to_local(image_url=image_url, image_path=image_path)
            self.__upload_image(gcs_path=gcs_path, local_image_path=image_path)
            self.__delete_local_image(image_path=image_path)
            j += 1

    def __upload_meld_image(self, card):
        for part in card["all_parts"]:
            if part["name"] == card["name"]:
                if part["component"] == "meld_result":
                    # 自身が合体カードの裏面の場合は特に何もせず終わる
                    continue
                else:
                    # 自身が合体カードの表面である場合はmain_imageとしてアップロード
                    self.__upload_normal_image(card)
            else:
                if part["component"] == "meld_result":
                    # 合体カードの裏面は情報を取得してsub_imageとしてアップロード
                    response = requests.get(part["uri"])
                    card_meld_result = json.loads(response.content.decode("utf-8"))

                    image_url = card_meld_result["image_uris"]["large"]
                    card_name = card["name"].replace("//", "__")
                    expansion = card["set"]
                    language = card["lang"]
                    collector_number = card["collector_number"]
                    gcs_path = self.__create_gcs_path(
                        language=language,
                        expansion=expansion,
                        collector_num=collector_number,
                        card_name=card_name,
                        is_sub=True,
                    )
                    print(card_name)
                    image_path = "{}.jpg".format(card_name)
                    self.__download_image_to_local(
                        image_url=image_url, image_path=image_path
                    )
                    self.__upload_image(gcs_path=gcs_path, local_image_path=image_path)
                    self.__delete_local_image(image_path=image_path)
                else:
                    # 自身以外の合体カードの表面はなにもしない
                    continue

    def main(self) -> None:
        print("START UPLOADING")
        failed = []
        with open(self.data_repo.JSON_FILE, "r", encoding="utf-8") as scryfall_json:
            for card in ijson.items(scryfall_json, "item"):
                image_type = self.data_repo.distribute_card_image_type(card)
                if image_type == "normal":
                    self.__upload_normal_image(card)
                elif image_type == "double":
                    self.__upload_double_image(card)
                elif image_type == "meld":
                    self.__upload_meld_image(card)
                elif image_type == "undefined":
                    failed.append(card["id"])
                else:
                    pass
        print(failed)


if __name__ == "__main__":
    func = ImageUploader()
    func.main()
