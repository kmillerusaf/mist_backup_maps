# Built-in imports
import csv
import getpass
import os
import sys
from datetime import datetime

# 3rd-party imports
import aiofiles
import asyncio
import httpx
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Script variables
curr_path = os.getcwd()
todays_date = datetime.now().strftime("%Y%m%d")
api_base_url = "https://CHANGE_ME/api/v1/" # Change FQDN in URL for your Mist region and cloud instance


async def download_ap_pics(ap_urls, file_path):
    async with httpx.AsyncClient() as client:
        try:
            for ap_url in ap_urls:
                for ap_name, url, in ap_url.items():
                    async with client.stream("GET", url, follow_redirects=True) as response:
                        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    
                        ap_dir = file_path + "/ap_pictures/"
                        if not os.path.isdir(ap_dir):
                            os.mkdir(ap_dir)
                        
                        full_path = os.path.join(ap_dir, ap_name)

                        if os.path.exists(full_path):
                            print("File already exists and download from Mist will be skipped.")
                        else: 
                            async with aiofiles.open(full_path, 'wb') as file:
                                async for chunk in response.aiter_bytes(1024):
                                    await file.write(chunk)
                                print(f"Image downloaded successfully to {full_path}")
        except response.exceptions.RequestException as e:
            print(f"Error downloading image from {url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


async def download_map(url, file_path, image_name):
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                map_dir = file_path + "/maps/"
                if not os.path.isdir(map_dir):
                    os.mkdir(map_dir)
                full_path = os.path.join(map_dir, image_name)

                if os.path.exists(full_path):
                    print("File already exists and download from Mist will be skipped.")
                else: 
                    async with aiofiles.open(full_path, 'wb') as file:
                        async for chunk in response.aiter_bytes(1024):
                            await file.write(chunk)
                    print(f"Image downloaded successfully to {full_path}")
                     
        except response.exceptions.RequestException as e:
            print(f"Error downloading image from {url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


async def get_site_aps(api_token, site_id):
    site_aps = {}

    headers = {"Authorization": f"Token {api_token}",
               "Content-type": "application/json",}
    
    url = api_base_url + f"sites/{site_id}/stats/devices?type=ap"

    with httpx.Client() as client:
        response = client.get(url, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            if len(json_data) > 0:
                for ap in json_data:
                    if ap["map_id"]:
                        ap_imgs = []
                        if ap.get("image1_url"):
                            img1 = ap["image1_url"]
                            ap_imgs.append(img1)
                        if ap.get("image2_url"):
                            img2 = ap["image2_url"]
                            ap_imgs.append(img2)
                        if ap.get("image3_url"):
                            img3 = ap["image3_url"]
                            ap_imgs.append(img3)
                        height = ap.get("height", "Not configured")
                        map_id = ap.get("map_id", "Not placed on map")
                        model = ap["model"]
                        mount = ap.get("mount", "Unknown")
                        orientation = ap.get("orientation", "Not configured")
                        x_coord = ap.get("x", "Unknown")
                        y_coord = ap.get("y", "Unknown")
                        
                        site_aps[ap["name"]] = {"height": height, "imgs": ap_imgs, "map_id": map_id , "model": model,
                                                "mount": mount, "orientation": orientation, "x": x_coord, "y": y_coord,}
                    else:
                        print(f"{ap['name']} has not been added to a map yet.")
        elif response.status_code == 299:
            print("You've exceeded the API rate limit for your token. Try again in the next hour.")
        else:
            print(f"Something went wrong trying to access the API @ {url}. Check your API token")
    return site_aps


def get_site_id(api_token, org_id, site_name):
    headers = {
        'Authorization': f'Token {api_token}',
        'Content-type': 'application/json'}
    
    url = api_base_url + f"orgs/{org_id}/sites/search?name={site_name}"
    
    response = httpx.get(url, headers=headers)

    if response.status_code == 200:
        json_data = response.json()
        if json_data["total"] == 1:
            site_id = json_data["results"][0]["id"]
            return site_id
        else:
            print(f"Site with name '{site_name}' was not found. Please try again.")
            sys.exit()
    elif response.status_code == 299:
        print("You've exceeded the API rate limit for your token. Try again in the next hour.")
    else:
        print(f"Something went wrong trying to access the API @ {url}. Check your API token")


def get_site_maps(api_token, site_id):
    headers = {"Authorization": f"Token {api_token}",
               "Content-type": "application/json",}

    url = api_base_url + f"sites/{site_id}/maps"

    response = httpx.get(url, headers=headers)

    if response.status_code == 200:
        site_maps = []
        json_data = response.json()
        if len(json_data) > 0:
            for map in json_data:
                site_maps.append({map["name"]: [map["id"], map["url"]]})
            return site_maps
        else:
            print("There are no maps uploaded for this site.")
    elif response.status_code() == 299:
        print("API token has exceeded its calls per hour limit. Try again later.")
    else:
        print(f"Something went wrong trying to access the API @ {url}. Check your API token")


def plot_aps(image_name, file_path, aps):
    convert_modes = ["CMYK", "L", "P", "RGBA"] # 'CMYK' is Cyan, Magenta, Yellow, and Black, 'L' is grayscale, 'P' is Indexed Color, 'RGBA' is transparency applied
    font_path = "/Library/Fonts/MartianMono-VariableFont_wdth,wght.ttf"
    img_path = file_path + "/maps/" + image_name
    try:
        img_font = ImageFont.truetype(font_path, 9)
    except FileNotFoundError:
        print("Error: Font file not found. Loading the default font.")
        ImageFont.load_default()
    except Exception as e:
        print(f"An error occurred: {e}")
            
    try:
        with Image.open(img_path) as img:
            img.load()
            img_mode = img.mode

            if img_mode in convert_modes:
                img_rgb = img.convert("RGB")
                draw = ImageDraw.Draw(img_rgb)
                print(f"{image_name} has been converted to RGB")
            else:
                draw = ImageDraw.Draw(img)
            
            coordinates = []
    
            number_of_devices = {}
            for ap in aps:
                for ap_name, ap_info in ap.items():
                    ap_model = ap_info["model"]
                    x = round(ap_info["x"], 3)
                    y = round(ap_info["y"], 3)
                    coordinates.append((ap_name, ap_model, x,y))
            for ap_name, ap_model, x, y in coordinates:
                radius = 10
                if number_of_devices.get(image_name, {}).get(ap_model, {}):
                    number_of_devices[image_name][ap_model] += 1          
                else:
                    number_of_devices[image_name] = {ap_model: 1}
                if "AP" in ap_model:
                    draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill="green") # Draw a green circle at each coordinate
                    draw.text((x + 7, y + 7), f"{ap_name}", fill="green", font=img_font) # Add AP name, use f"{ap_name}\n({x}, {y})" to add coordinates
                elif "BT" in ap_model:
                    draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill="blue") # Draw a blue circle at each coordinate
                    draw.text((x + 7, y + 7), f"{ap_name}", fill="blue", font=img_font) # Add AP name, use f"{ap_name}\n({x}, {y})" to add coordinates

            for map, device_info in number_of_devices.items():
                for device_type, num_of_devices in device_info.items():
                    print(f"{map} has {num_of_devices} {device_type}s on the map.")

            save_img = img_path.replace(".jpeg", "")
            if "img_rgb" in locals():
                img_rgb.save(save_img + "-AP_locations.png")
            else:
                img.save(save_img + "-AP_locations.png")
    except FileNotFoundError as e:
        print(f"An unexpected error occurred: {e}")


def main():
    try:
        load_dotenv()
        api_token = os.getenv("MIST_API_TOKEN")
        org_id = os.getenv("MIST_ORG_ID")
    except Exception as e:
        print(e)
    
    if api_token is None:
        print("API token was not found in a .env file.")
        api_token = getpass.getpass("Please enter your API token: ")

    if org_id is None:
        print("Your Mist org ID was not found in a .env file.")
        org_id = input("Please enter your Mist org ID: ")
    
    backup_site = input("What site would you like to backup maps for?: ")

    site_id = get_site_id(api_token, org_id, backup_site)

    if site_id:
        site_maps = get_site_maps(api_token, site_id)

        if site_maps:
            site_map_ids = {}
            site_dir = curr_path + "/" + backup_site
            if not os.path.isdir(site_dir):
                os.mkdir(site_dir)
            
            for map in site_maps:
                for map_name, map_info in map.items():
                    image_name = map_name + ".jpeg"
                    image_id = map_info[0]
                    image_url = map_info[1]
                    asyncio.run(download_map(image_url, site_dir, image_name))
                    site_map_ids[image_name] = image_id
            
            site_aps = asyncio.run(get_site_aps(api_token, site_id))

            if site_aps:
                aps_by_map = {}
                with open(f"{site_dir}/{backup_site}-APs-{todays_date}.csv", "w") as csvfile:
                    csv_file = csv.writer(csvfile)
                    csv_file.writerow(["AP Name", "Model", "Map ID", "Height", "Mount", "Orientation",
                                        "X Coord", "Y Coord"])
                    for ap, ap_info in site_aps.items():
                        img_url_counter = 1
                        ap_urls = []
                        for url in ap_info["imgs"]:
                            ap_image_name = ap + "-img" + str(img_url_counter) + ".jpeg"
                            ap_urls.append({ap_image_name: url})
                            img_url_counter += 1
                        asyncio.run(download_ap_pics(ap_urls, site_dir))

                        for map_name, img_id in site_map_ids.items():
                            if ap_info["map_id"] == img_id:
                                if aps_by_map.get(map_name):
                                    aps_by_map[map_name].append({ap: ap_info})
                                else:
                                    aps_by_map[map_name] = [{ap: ap_info}]
                
                        csv_file.writerow([ap, ap_info["model"], img_id, ap_info["height"], ap_info["mount"],
                                           ap_info["orientation"], ap_info["x"], ap_info["y"]])

                if aps_by_map:
                    for map_name, aps in aps_by_map.items():
                        map_image = map_name
                        plot_aps(map_image, site_dir, aps)


if __name__ == "__main__":
    main()
