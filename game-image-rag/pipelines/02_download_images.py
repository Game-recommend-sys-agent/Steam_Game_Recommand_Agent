import json
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO

# ===============================
# Config
# ===============================
STORE_API_DIR = Path("data/store_api")
OUTPUT_DIR = Path("data/images")

# 요청 타임아웃
REQUEST_TIMEOUT = 10

# ===============================
# Utils
# ===============================
def load_store_api_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_image_url(store_data: dict, appid: int):
    """
    이미지 우선순위:
    1. header_image
    2. capsule_image
    3. capsule_imagev5
    """
    app_data = store_data[str(appid)]["data"]

    if app_data.get("header_image"):
        return app_data["header_image"]

    if app_data.get("capsule_image"):
        return app_data["capsule_image"]

    if app_data.get("capsule_imagev5"):
        return app_data["capsule_imagev5"]

    return None


def download_image(url: str):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


def save_image(image: Image.Image, path: Path):
    image.save(path, format="JPEG", quality=95)


# ===============================
# Main
# ===============================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    store_files = list(STORE_API_DIR.glob("*.json"))
    print(f"[INFO] Found {len(store_files)} Store API files")

    for store_file in store_files:
        appid = int(store_file.stem)
        output_path = OUTPUT_DIR / f"{appid}.jpg"

        if output_path.exists():
            print(f"[SKIP] Image already exists for appid={appid}")
            continue

        try:
            store_data = load_store_api_json(store_file)
            image_url = extract_image_url(store_data, appid)

            if not image_url:
                print(f"[WARN] No image URL found for appid={appid}")
                continue

            print(f"[DOWNLOAD] appid={appid}")
            image = download_image(image_url)
            save_image(image, output_path)

        except Exception as e:
            print(f"[ERROR] Failed to process appid={appid}: {e}")

    print("[DONE] Image download completed")


if __name__ == "__main__":
    main()
