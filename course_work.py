import requests
import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
import requests
import sys
load_dotenv()
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
VK_TOKEN1 = os.environ.get("VK_TOKEN1")

class VkDownloader:
    def __init__(self, token):
        self.token = token
        self.user_id = None

    def get_photos(self, user_id):
        self.user_id = user_id
        url = "https://api.vk.com/method/photos.get"
        params = {
            "owner_id": user_id,
            "album_id": "profile",
            "access_token": self.token,
            "v": "5.131",
            "extended": "1",
            "photo_sizes": "1",
        }
        res = requests.get(url=url, params=params)
        return res.json()

    def get_all_photos(self):
        photos_count = 0
        photos = []
        max_size_photo = {}

        if not os.path.exists("images_vk"):
            os.mkdir("images_vk")

        max_photos = 5

        while photos_count < max_photos:
            data = self.get_photos(self.user_id)

            if "response" in data and "items" in data["response"]:
                for photo in data["response"]["items"]:
                    max_size = 0
                    photos_info = {}
                    for size in photo["sizes"]:
                        if size["height"] >= max_size:
                            max_size = size["height"]

                    if photo["likes"]["count"] not in max_size_photo.keys():
                        max_size_photo[photo["likes"]["count"]] = size["url"]
                        if len(max_size_photo) == max_photos:
                            photos_info["file_name"] = f"{photo['likes']['count']}+{photo['date']}.jpg"
                        else:
                            photos_info["file_name"] = f"{photo['likes']['count']}.jpg"
                    else:
                        max_size_photo[
                            f"{photo['likes']['count']} + {photo['date']}"
                        ] = size["url"]
                        photos_info[
                            "file_name"
                        ] = f"{photo['likes']['count']}+{photo['date']}.jpg"

                    photos_info["size"] = size["type"]
                    photos.append(photos_info)

            else:
                print("Ошибка при получении фотографий. Пожалуйста, проверьте правильность введенного ID пользователя VK.")
                print("Ответ VK API:", data)
                sys.exit(1)

            for photo_name, photo_url in max_size_photo.items():
                with open("images_vk/%s" % f"{photo_name}.jpg", "wb") as file:
                    img = requests.get(photo_url)
                    file.write(img.content)

            print(f"Загружено {len(max_size_photo)} фото")
            photos_count += len(max_size_photo)
            

        with open("photos.json", "w") as file:
            json.dump(photos, file, indent=4)

class YaUploader:
    def __init__(self, ya_token: str):
        self.ya_token = ya_token

    def create_folder(self, ya_folder_name):
        url = f"https://cloud-api.yandex.net/v1/disk/resources"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"OAuth {self.ya_token}",
        }
        params = {"path": f"{ya_folder_name}", "overwrite": "false"}
        response = requests.put(url=url, headers=headers, params=params)

    def upload(self, file_path: str, ya_folder_name, file_name):
        url = f"https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"OAuth {self.ya_token}",
        }
        params = {"path": f"{ya_folder_name}/{file_name}", "overwrite": "true"}

        response = requests.get(url=url, headers=headers, params=params)
        href = response.json().get("href")

        uploader = requests.put(href, data=open(file_path, "rb"))

def main():
    user_id = str(input("Введите id пользователя VK: "))
    downloader = VkDownloader(VK_TOKEN1)
    downloader.get_all_photos()

    ya_token = str(input("Введите ваш токен ЯндексДиск: "))
    uploader = YaUploader(ya_token)
    ya_folder_name = str(
        input(
            "Введите имя папки на Яндекс диске, в которую необходимо сохранить фото: "
        )
    )
    uploader.create_folder(ya_folder_name)

    photos_list = os.listdir("images_vk")[:5]  
    count = 0
    with tqdm(total=len(photos_list), ncols=100, desc="Uploading") as pbar:
        for photo in photos_list:
            file_name = photo
            file_path = os.path.join(os.getcwd(), 'images_vk', photo)
            uploader.upload(file_path, ya_folder_name, file_name)
            count += 1
            pbar.update(1)
            pbar.set_postfix({"Uploaded": count})

if __name__ == "__main__":
    main()