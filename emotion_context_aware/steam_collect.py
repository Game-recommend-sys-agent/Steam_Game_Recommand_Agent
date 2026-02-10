import re
import json
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ===============================
# 1. Steam Store API – 게임 메타
# ===============================
def fetch_game_meta(game_appid: str):
    url = f"https://store.steampowered.com/api/appdetails?appids={game_appid}&l=en"
    data = requests.get(url, headers=HEADERS).json()

    if not data.get(game_appid, {}).get("success"):
        return None

    app = data[game_appid]["data"]

    genres = [g["description"] for g in app.get("genres", [])]
    description = BeautifulSoup(
        app.get("short_description", ""), "html.parser"
    ).get_text(" ", strip=True)

    return {
        "appid": game_appid,
        "name": app.get("name"),
        "genres": genres,
        "description": description
    }


# ===============================
# 2. 게임 페이지 → OST appid 찾기
# ===============================
def find_ost_appid(game_appid: str):
    url = f"https://store.steampowered.com/app/{game_appid}/"
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")

    for a in soup.select("a[href*='/app/']"):
        text = a.get_text(strip=True).lower()
        if "soundtrack" in text or "ost" in text:
            m = re.search(r"/app/(\d+)", a.get("href", ""))
            if m:
                return m.group(1)

    return None


# ===============================
# 3. 게임 태그 (Store Page)
# ===============================
def extract_game_tags(game_appid: str):
    url = f"https://store.steampowered.com/app/{game_appid}/"
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")
    tags = [t.get_text(strip=True) for t in soup.select(".app_tag")]
    return list(dict.fromkeys(tags))


# ===============================
# 4. OST 트랙리스트 (Playwright)
# ===============================
def extract_ost_tracks_playwright(ost_appid: str):
    url = f"https://store.steampowered.com/app/{ost_appid}/"
    tracks = []
    dur_re = re.compile(r"^\d{1,2}:\d{2}$")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")

        container_sel = "#music_album_area_description .music_album_track_list_contents"
        page.wait_for_selector(container_sel, timeout=15000)

        container = page.query_selector(container_sel)
        divs = container.query_selector_all("div")

        seen = set()

        for d in divs:
            lines = [x.strip() for x in d.inner_text().split("\n") if x.strip()]
            if len(lines) < 3:
                continue

            if lines[0].isdigit() and dur_re.match(lines[-1]):
                track_no = int(lines[0])
                duration = lines[-1]
                title = " ".join(lines[1:-1]).strip()

                # ❌ 전체 트랙 덤프 제거
                if len(re.findall(r"\d{1,2}:\d{2}", title)) > 1:
                    continue

                key = (track_no, title, duration)
                if key in seen:
                    continue
                seen.add(key)

                tracks.append({
                    "order": track_no,
                    "title": title,
                    "duration": duration
                })

        browser.close()

    tracks.sort(key=lambda x: x["order"])
    return tracks


# ===============================
# 5. 통합 수집 파이프라인
# ===============================
def collect_game_narrative_inputs(game_appid: str):
    game_meta = fetch_game_meta(game_appid)
    if not game_meta:
        raise RuntimeError("게임 메타 수집 실패")

    game_meta["game_tags"] = extract_game_tags(game_appid)

    ost_appid = find_ost_appid(game_appid)
    soundtrack = None

    if ost_appid:
        soundtrack = {
            "ost_appid": ost_appid,
            "tracks": extract_ost_tracks_playwright(ost_appid)
        }

    return {
        "game_meta": game_meta,
        "soundtrack": soundtrack
    }


# ===============================
# 6. 🔹 LLM 입력용 정규화 페이로드
# ===============================
def build_llm_payload(collected_data: dict):
    return {
        "game_meta": {
            "genres": collected_data["game_meta"]["genres"],
            "tags": collected_data["game_meta"]["game_tags"],
            "description": collected_data["game_meta"]["description"]
        },
        "soundtrack": {
            "tracks": collected_data["soundtrack"]["tracks"]
        }
    }


# ===============================
# 7. 실행부
# ===============================
if __name__ == "__main__":
    GAME_APPID = "1641960"  # Forever Skies

    raw_data = collect_game_narrative_inputs(GAME_APPID)
    llm_payload = build_llm_payload(raw_data)

    print("=== RAW DATA ===")
    print(json.dumps(raw_data, indent=2, ensure_ascii=False))

    print("\n=== LLM PAYLOAD ===")
    print(json.dumps(llm_payload, indent=2, ensure_ascii=False))