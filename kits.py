import os, subprocess, uuid

from flask import Flask, request
from PIL import Image
import requests
from requests.exceptions import HTTPError

app = Flask(__name__)


@app.route("/kit", methods=["POST"])
def kit():
    data = request.json
    tile = TileKits(data)
    tile.request_assets()
    tile.create_overlay()
    tile.create_items()
    return data


class TileKits(object):
    def __init__(self, data):
        self.id = str(uuid.uuid4())
        self.data = data

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
        for item in self.data["items"]:
            subprocess.run(
                [
                    "convert",
                    f"{self.id}/item_bkgd.png",
                    "(",
                    f"sprites/{item}.png",
                    "-scale",
                    "192x192",
                    "-geometry",
                    "+32+10",
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
                    "-fill",
                    "white",
                    "-font",
                    "Permanent-Marker",
                    "-pointsize",
                    "48",
                    "-strokewidth",
                    "5",
                    "-stroke",
                    "black",
                    "-geometry",
                    "-160-160",
                    f"label:x{self.data['items'][item]}",
                    f"{self.id}/items/item-{item}x.png",
                ]
            )