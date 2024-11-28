#!/usr/bin/env python3

import requests
from pathlib import Path
from subprocess import run


"""
Goals
- Only download the image if I don't already have it
- Be able to see the description of the image
- Know the images for the previous days
"""


class ImageListing:
    """
    The NASA Picture Of the Day URL is different for each day.
    There is an API that can be hit to get the URL of the image for the day.
    This class will hold the information that is returned from the API which is
    needed to download the image.
    """

    def __init__(self, contents: dict[str, str] = {}):
        self.from_api_resp_json(contents)

    def from_api_resp_json(self, json: dict[str, str]):
        self.date = json.get("date", "")
        self.explanation = json.get("explanation", "")
        self.media_type = json.get("media_type", "")
        self.title = json.get("title", "")
        self.url = json.get("hdurl", "")

    @property
    def is_image(self) -> bool:
        return self.media_type == "image"

    @property
    def save_name(self) -> str:
        remote_file_name = self.url.split("/")[-1]
        return f"{self.date}_{remote_file_name}"


def get_image_listing(api_key: str) -> ImageListing:
    # Perform the query
    api_url = "https://api.nasa.gov/planetary/apod?api_key={}"
    get_apod_resp = requests.get(api_url.format(api_key))
    get_apod_resp_dict = {}
    if get_apod_resp is not None:
        get_apod_resp_dict = get_apod_resp.json()
    else:
        raise Exception("Failed to hit apod endpoint")

    # Check the api key was correct
    if "error" in get_apod_resp_dict:
        raise Exception(
            "API call was invalid but to the correct endpoint."
            f" error returned [{get_apod_resp_dict["error"]["code"]}]"
        )

    return ImageListing(get_apod_resp.json())


def get_image(image_listing: ImageListing) -> bytes:
    """
    Get the image from the remote server.
    """

    img_resp = requests.get(image_listing.url)
    if img_resp is None:
        raise Exception("Failed to hit image endpoint")

    return img_resp.content


def main(api_key: str = None):
    # Sanity Checking
    # API key is required
    if api_key is None:
        print("No API key provided")
        exit(1)
    # Image Setting Script is required
    wallpaper_script = Path("./setWallpaper.sh").resolve()
    if not wallpaper_script.is_file():
        print("Wallpaper setting script not found")
        exit(1)

    # Get the image request from NASA
    print("Getting daily-image listing")
    try:
        img_listing = get_image_listing(api_key)
    except Exception as e:
        print(f"Failed to get image listing: {e}")
        exit(1)
    else:
        print(f"\tTitle: {img_listing.title}")

    if not img_listing.is_image:
        print("Not an image today")
        exit(1)

    # Determine if there is a new image to get
    # Regretfully, the name of the directory that holds the image is the name
    # of the image file itself.
    print("Downloading image")
    images_save_dir = Path("~/APOD").expanduser()
    links_save_dir = Path("~/Pictures/APOD").expanduser()
    img_save_location = images_save_dir / img_listing.save_name
    link_save_location = links_save_dir / img_listing.save_name
    if not img_save_location.exists():
        img_save_location.mkdir(parents=True)

        # Get the image data from NASA and save to disk
        img_data = get_image(img_listing)
        img_file_extension = "." + img_listing.url.split(".")[-1]
        (img_save_location / "image").with_suffix(
            img_file_extension
        ).write_bytes(img_data)
        (img_save_location / "description.txt").write_text(
            f"{img_listing.title}\n\n{img_listing.explanation}\n"
        )
        link_save_location.symlink_to(img_save_location / "image")
    else:
        print("The image does not need to be downloaded")

    # Make image into the wallpaper
    print("Setting wallpaper")
    run(
        [
            wallpaper_script,
            str(link_save_location),
        ]
    )


if __name__ == "__main__":
    with Path("./api_key.txt").open() as f:
        api_key = f.read().strip("\n")

    main(api_key)
