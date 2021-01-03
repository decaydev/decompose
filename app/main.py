import os, subprocess, uuid

from flask import Flask, request, send_file
from PIL import Image
import requests
from requests.exceptions import HTTPError


app = Flask(__name__)

blob = requests.get("https://decaydev.blob.core.windows.net/data/items.json")
items = blob.json()

def search_item(shortname):
    return next((item for item in items["items"] if item["shortname"] == shortname), False)


@app.route("/kit", methods=["PUT"])
def kit():
    data = request.json
    tile = TileKits(data)
    tile.request_assets()
    tile.create_overlay()
    tile.create_items()
    tile.create_montage()
    tile.create_kit()
    tile.pngquant()
    return send_file(f"{tile.id}/kit.png", mimetype="image/png")


@app.route("/banner", methods=["PUT"])
def banner():
    data = request.json
    tile = TileBanner(data)
    tile.request_assets()
    tile.create_overlay()
    #tile.pngquant()
    return send_file(f"{tile.id}/output.png", mimetype="image/png")


class TileBanner(object):
    def __init__(self, data):
        self.id = str(uuid.uuid4())
        self.data = data

    def request_assets(self):
        os.mkdir(self.id)
        try:
            r = requests.get(self.data["banner"])
            r.raise_for_status()
        except HTTPError:
            raise Exception(f"unable to download: {banner}")
        open(f"{self.id}/banner.png", "wb").write(r.content)

    def create_overlay(self):
        subprocess.run(
            [
                "convert",
                f"{self.id}/banner.png",
                "-background",
                "None",
                "-font",
                f"{self.data['font']}",
                "-pointsize",
                "90",
                "-fill",
                "black",
                "-stroke",
                "black",
                "-strokewidth",
                "19",
                "-annotate",
                f"{self.data['annotate']}",
                f"{self.data['steam_displayname']}",
                "-fill",
                "white",
                "-stroke",
                "white",
                "-strokewidth",
                "1",
                "-annotate",
                f"{self.data['annotate']}",
                f"{self.data['steam_displayname']}",
                f"{self.id}/output.png",
            ]
        )


class TileKits(object):
    def __init__(self, data):
        self.id = str(uuid.uuid4())
        self.data = data
        self.items = items["items"]
        self.item_count = len(self.data["items"])

    def request_assets(self):
        os.mkdir(self.id)
        for asset in self.data["imgs"]:
            try:
                r = requests.get(self.data["imgs"][asset]["url"])
                r.raise_for_status()
            except HTTPError:
                raise Exception(f"unable to download asset: {asset}")
            open(f"{self.id}/{asset}.png", "wb").write(r.content)
            self.validate_asset(asset)

    def validate_asset(self, asset):
        d = self.data["imgs"][asset]
        with Image.open(f"{self.id}/{asset}.png") as (img):
            width, height = img.size
            if d["width"] == width and d["height"] == height:
                pass
            else:
                raise Exception(f"invalid image dimensions for {asset}")

    def create_overlay(self):
        subprocess.run(
            [
                "convert",
                f"{self.id}/kits_bkgd.png",
                "(",
                f"{self.id}/kits_icon.png",
                "-scale",
                "384x384",
                "-geometry",
                "+320+96",
                "-background",
                "None",
                ")",
                "-background",
                "None",
                "-composite",
                f"{self.id}/kits_tile.png",
            ]
        )

    def create_items(self):
        os.mkdir(f"{self.id}/items")

        for index, item in enumerate(self.data["items"]):
            stack = self.data["items"][item]
            sprite = search_item(item)

            # zfill filename for imagemagick(shell glob)
            index += 1
            if index <= 9:
                num = str(index).zfill(2)
            else:
                num = index

            if stack <= 1:
                annotate = 390
            elif stack >= 2 and stack <= 9:
                annotate = 370
            elif stack >= 10 and stack <= 99:
                annotate = 320
            elif stack >= 100 and stack <= 999:
                annotate = 250
            elif stack >= 1000 and stack <= 9999:
                annotate = 200
            elif stack >= 10000 and stack <= 99999:
                annotate = 130
            elif stack >= 100000 and stack <= 999999:
                annotate = 70
            elif stack >= 1000000 and stack <= 9999999:
                annotate = 40
            subprocess.run(
                [
                    "convert",
                    f"{self.id}/item_bkgd.png",
                    "(",
                    f"sprites/{sprite['spriteName']}.png",
                    "-scale",
                    "384x384",
                    "-geometry",
                    "+64+50",
                    "-background",
                    "None",
                    ")",
                    "-background",
                    "None",
                    "-composite",
                    f"{self.id}/items/item-{item}.png",
                ]
            )
            subprocess.run(
                [
                    "convert",
                    f"{self.id}/items/item-{item}.png",
                    "-background",
                    "None",
                    "-font",
                    "PermanentMarker.ttf",
                    "-pointsize",
                    "90",
                    "-fill",
                    "black",
                    "-stroke",
                    "black",
                    "-strokewidth",
                    "19",
                    "-annotate",
                    f"+{annotate}+485",
                    f"x{self.data['items'][item]}",
                    "-fill",
                    "white",
                    "-stroke",
                    "white",
                    "-strokewidth",
                    "1",
                    "-annotate",
                    f"+{annotate}+485",
                    f"x{self.data['items'][item]}",
                    f"{self.id}/items/item_{num}.png",
                ]
            )
            os.remove(f"{self.id}/items/item-{item}.png")

    def create_montage(self):
        if self.item_count <= 1:
            tile = "1x1"
            geometry = "700x700+20+20"
        elif self.item_count == 2:
            tile = "1x2"
            geometry = "700x700+20+20"
        elif self.item_count >= 3 and self.item_count <= 4:
            tile = "2x2"
            geometry = "460x460+20+20"
        elif self.item_count >= 5 and self.item_count <= 9:
            tile = "3x3"
            geometry = "293x293+20+20"
        elif self.item_count >= 10 and self.item_count <= 12:
            tile = "3x4"
            geometry = "293x293+20+20"
        elif self.item_count >= 13 and self.item_count <= 16:
            tile = "4x4"
            geometry = "210x210+20+20"
        elif self.item_count >= 17 and self.item_count <= 20:
            tile = "4x5"
            geometry = "210x210+20+20"
        elif self.item_count >= 21 and self.item_count <= 24:
            tile = "4x6"
            geometry = "210x210+20+20"
        elif self.item_count == 25:
            tile = "5x5"
            geometry = "180x180+10+10"
        elif self.item_count >= 26 and self.item_count <= 30:
            tile = "5x6"
            geometry = "180x180+10+10"
        elif self.item_count >= 31 and self.item_count <= 35:
            tile = "5x7"
            geometry = "180x180+10+10"
        subprocess.run(
            [
                "montage",
                f"{self.id}/items/item_*",
                "-background",
                "None",
                "-tile",
                f"{tile}",
                "-geometry",
                f"{geometry}",
                f"{self.id}/items/montage.png",
            ]
        )

    def create_kit(self):
        if self.item_count <= 1 or self.item_count <= 2:
            geometry = "+142+556"
        elif self.item_count >= 3 and self.item_count <= 24:
            geometry = "+12+556"
        elif self.item_count >= 25 and self.item_count <= 35:
            geometry = "+12+566"
        subprocess.run(
            [
                "convert",
                f"{self.id}/kits_tile.png",
                "(",
                f"{self.id}/items/montage.png",
                "-geometry",
                f"{geometry}",
                "-background",
                "None",
                ")",
                "-background",
                "None",
                "-composite",
                f"{self.id}/tile.png",
            ]
        )

    def pngquant(self):
        subprocess.run(
            [
                "pngquant",
                "--strip",
                f"{self.id}/tile.png",
                "-o",
                f"{self.id}/kit.png",
            ]
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=80)

