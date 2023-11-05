import math
import sys
import aiohttp
import asyncio
import os
import rasterio
from PIL import Image

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def read_config(filename="config.csv"):
    config_data = {}
    keys = ["lat1", "lon1", "lat2", "lon2", "zoom"]

    with open(filename, "r", encoding="utf-8") as csvfile:
        line = csvfile.readline()
        values = line.strip().split(",")
        config_data = {keys[i]: float(values[i].strip()) for i in range(len(keys))}

    return config_data


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)


async def download_tile(session, x, y, zoom, semaphore, folder="tiles"):
    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
    headers = {"User-Agent": "MapDownloadApp/1.0 (onukevich22@gmail.com)"}
    async with semaphore:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                content = await response.read()
                filename = f"{folder}/{zoom}_{x}_{y}.png"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, "wb") as f:
                    f.write(content)
                print(f"Downloaded tile {zoom}/{x}/{y}")
            else:
                print(
                    f"Error while download tile {zoom}/{x}/{y}: HTTP {response.status}"
                )


async def download_tiles(lat1, lon1, lat2, lon2, zoom):
    semaphore = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        x_start, y_start = deg2num(lat1, lon1, zoom)
        x_end, y_end = deg2num(lat2, lon2, zoom)
        tasks = []
        for x in range(min(x_start, x_end), max(x_start, x_end) + 1):
            for y in range(min(y_start, y_end), max(y_start, y_end) + 1):
                task = asyncio.create_task(
                    download_tile(session, x, y, zoom, semaphore)
                )
                tasks.append(task)
        await asyncio.gather(*tasks)


def combine_tiles(zoom, lat1, lon1, lat2, lon2):
    output_folder = "map"

    x_start, y_start = deg2num(lat1, lon1, zoom)
    x_end, y_end = deg2num(lat2, lon2, zoom)
    x_start, x_end = min(x_start, x_end), max(x_start, x_end)
    y_start, y_end = min(y_start, y_end), max(y_start, y_end)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_filename = os.path.join(output_folder, "combined_map.png")

    width = (x_end - x_start + 1) * 256
    height = (y_end - y_start + 1) * 256

    combined_image = Image.new("RGB", (width, height))

    tile_folder = "tiles"

    for x in range(x_start, x_end + 1):
        for y in range(y_start, y_end + 1):
            tile_path = os.path.join(tile_folder, f"{zoom}_{x}_{y}.png")
            try:
                tile_image = Image.open(tile_path)

                combined_image.paste(
                    tile_image, ((x - x_start) * 256, (y - y_start) * 256)
                )
            except FileNotFoundError:
                print(f"Tile at {tile_path} not found.")

    combined_image.save(output_filename)
    print("Map combined")


def georeference_image(lon1, lat1, lon2, lat2):
    with rasterio.open("map/combined_map.png") as src:
        data = src.read()
        width = src.width
        height = src.height

    res_x = (lon1 - lon2) / width
    res_y = (lat1 - lat2) / height

    transform = rasterio.transform.from_origin(lon2, lat1, res_x, abs(res_y))

    new_dataset_meta = src.meta.copy()
    new_dataset_meta.update(
        {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "transform": transform,
            "crs": "EPSG:4326",
        }
    )

    with rasterio.open("map/combined_map.tif", "w", **new_dataset_meta) as dest:
        dest.write(data)

    print("Map is georeferenced")


async def main():
    data = read_config()
    lat1 = data.get("lat1")
    lon1 = data.get("lon1")
    lat2 = data.get("lat2")
    lon2 = data.get("lon2")
    zoom = int(data.get("zoom"))

    await download_tiles(lat1, lon1, lat2, lon2, zoom)
    combine_tiles(zoom, lat1, lon1, lat2, lon2)
    georeference_image(lat1, lon1, lat2, lon2)


asyncio.run(main())
