import json
import time
import requests
from pathlib import Path

# ===============================
# Config
# ===============================
CANDIDATE_FILE = Path("data/candidates/phase2_3_candidates.json")
OUTPUT_DIR = Path("data/store_api")
STORE_API_URL = "https://store.steampowered.com/api/appdetails"

# 안정성을 위해 언어/국가 고정
DEFAULT_PARAMS = {
    "l": "english",
    "cc": "us"
}

# 요청 간 딜레이 (비공식 API 보호)
REQUEST_DELAY = 1.0  # seconds

# ===============================
# Utils
# ===============================
def load_candidate_appids(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["candidate_appids"]


def fetch_store_api(appid: int):
    params = {
        "appids": appid,
        **DEFAULT_PARAMS
    }
    response = requests.get(STORE_API_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def save_json(data: dict, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===============================
# Main
# ===============================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    appids = load_candidate_appids(CANDIDATE_FILE)
    print(f"[INFO] Fetching Store API data for {len(appids)} games")

    for idx, appid in enumerate(appids, start=1):
        output_path = OUTPUT_DIR / f"{appid}.json"

        if output_path.exists():
            print(f"[SKIP] {appid} already exists")
            continue

        try:
            print(f"[{idx}/{len(appids)}] Fetching appid={appid}")
            data = fetch_store_api(appid)

            # 기본 sanity check
            if str(appid) not in data:
                print(f"[WARN] Invalid response structure for appid={appid}")
                continue

            if not data[str(appid)].get("success", False):
                print(f"[WARN] Store API returned success=false for appid={appid}")
                continue

            save_json(data, output_path)

        except Exception as e:
            print(f"[ERROR] Failed to fetch appid={appid}: {e}")

        time.sleep(REQUEST_DELAY)

    print("[DONE] Store API fetching completed")


if __name__ == "__main__":
    main()
