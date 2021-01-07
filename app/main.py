import os
import shutil
import subprocess
import uuid
import requests
from flask import Flask, request, send_file, after_this_request


app = Flask(__name__)


blob = requests.get("https://decaydev.blob.core.windows.net/data/items.json")
items = blob.json()

def search_item(shortname):
    return next((item for item in items["items"] if item["shortname"] == shortname), False)

@app.route("/api", methods=["PUT"])
def decompose():
    data = request.json
    resp = Decompose(data)

    @after_this_request
    def cleanup(f):
        shutil.rmtree(f"{resp.id}/")
        return f

    return send_file(f"{resp.id}/output.png", mimetype="image/png")
   

class Decompose(object):
    def __init__(self, data):
        self.id = str(uuid.uuid4())
        for attr, value in data.items():
            setattr(self, attr, value)
        if self.type == "banner":
            self.banner(self.attrs["text"])
        elif self.type == "kit":
            self.size = len(self.attrs["items"])
            self.kit()
        self.pngquant()

    def banner(self, text):
        self.stroke(text, None, "pre.png")

    def kit(self):
        name,kit = self.name.split("/")

        self.overlay(
            f"sprites/kits/{name}/bkgd.png",
            f"sprites/kits/{name}/kit_{kit}.png",
            "bkgd.png",
        )

        for index, item in enumerate(self.attrs["items"]):
            sprite = search_item(item)
            text = self.attrs["items"][item]

            index += 1
            if index <= 9:
                num = str(index).zfill(2)
            else:
                num = index

            self.overlay(
                f"sprites/kits/{name}/item_bkgd.png",
                f"sprites/{sprite['spriteName']}.png",
                f"items/pre-{num}.png"
            )
            self.stroke(
                f"x{text}",
                f"{self.id}/items/pre-{num}.png",
                f"items/item-{num}.png"
            )
            self.montage()
        self.overlay(f"{self.id}/bkgd.png", f"{self.id}/montage.png", f"pre.png")
        

    def pngquant(self):
        subprocess.run(
            [
                "pngquant",
                "--strip",
                f"{self.id}/pre.png",
                "-o",
                f"{self.id}/output.png",
            ]
        )

    def montage(self):
        subprocess.run(
            [
                "scripts/montage",
                "--type",
                f"{self.type}",
                "--name",
                f"{self.name}",
                "--uuid",
                f"{self.id}",
                "--size",
                f"{self.size}"                                
            ]
        )

    def overlay(self, img, over, output="overlay.png"):
        subprocess.run(
            [
                "scripts/overlay",
                "--type",
                f"{self.type}",
                "--name",
                f"{self.name}",
                "--uuid",
                f"{self.id}",
                "--size",
                f"{self.size}",
                "--img",
                f"{img}",
                "--over",
                f"{over}",
                "--output",
                f"{output}"                                               
            ]
        )

    def stroke(self, text, img=None, output="pre.png"):
        subprocess.run(
            [
                "scripts/stroke",
                "--type",
                f"{self.type}",
                "--name",
                f"{self.name}",
                "--uuid",
                f"{self.id}",
                "--output",
                f"{output}",
                "--text",
                f"{text}",
                "--img",
                f"{img}"
            ]
        )
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=80)
