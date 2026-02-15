# filters/steam_api.py
import requests
import time

STEAM_API_URL = "https://store.steampowered.com/api/appdetails"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

def fetch_app_details(
    appid: int,
    sleep_sec: float = 0.6,      # 🔥 기본 속도 낮춤
    max_retry: int = 3,
) -> dict | None:
    for attempt in range(max_retry):
        try:
            resp = requests.get(
                STEAM_API_URL,
                params={"appids": appid, "cc": "kr", "l": "english"},
                headers=HEADERS,
                timeout=10,
            )

            if resp.status_code == 200:
                data = resp.json()
                app_block = data.get(str(appid))
                if app_block and app_block.get("success") and app_block.get("data"):
                    return app_block["data"]
                return None

            elif resp.status_code == 429:
                # 🔁 backoff
                wait = sleep_sec * (2 ** attempt)
                print(f"[API 429] appid={appid}, retry in {wait:.1f}s")
                time.sleep(wait)
                continue

            else:
                print(f"[API FAIL] appid={appid}, status={resp.status_code}")
                return None

        except Exception as e:
            print(f"[API EXCEPTION] appid={appid}, error={e}")
            return None

    return None