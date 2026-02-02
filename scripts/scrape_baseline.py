import requests
import pandas as pd
from datetime import datetime
from collections import Counter


class GameContextPipelineV4:
    """
    Steam + IGDB 기반
    '추천 시스템 중심' 유저 컨텍스트 & 성향 벡터 생성 파이프라인
    유저 하드웨어 스펙 입력 가능 (CPU, GPU, RAM, OS, 저장 공간)
    """

    def __init__(self, steam_api_key, igdb_client_id, igdb_client_secret):
        self.steam_key = steam_api_key
        self.client_id = igdb_client_id
        self.client_secret = igdb_client_secret
        self.igdb_access_token = self._get_igdb_token()
        self.igdb_auth = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.igdb_access_token}"
        }

    # =========================================================
    # IGDB TOKEN
    # =========================================================
    def _get_igdb_token(self):
        res = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
        )
        res.raise_for_status()
        return res.json()["access_token"]

    # =========================================================
    # STEAM APIs
    # =========================================================
    def get_recent_games(self, steam_id):
        url = "http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
        params = {"key": self.steam_key, "steamid": steam_id, "format": "json"}
        return requests.get(url, params=params).json().get("response", {}).get("games", [])

    def get_owned_games(self, steam_id):
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": self.steam_key,
            "steamid": steam_id,
            "include_appinfo": True,
            "format": "json"
        }
        return requests.get(url, params=params).json().get("response", {}).get("games", [])

    # =========================================================
    # IGDB GAME METADATA
    # =========================================================
    def get_game_metadata(self, game_name):
        query = f"""
        fields
            genres.name,
            themes.name,
            game_modes.name,
            player_perspectives.name,
            total_rating;
        where name ~ "{game_name}"*;
        limit 1;
        """
        res = requests.post(
            "https://api.igdb.com/v4/games",
            headers=self.igdb_auth,
            data=query
        )
        res.raise_for_status()
        data = res.json()
        return data[0] if data else {}

    # =========================================================
    # PLAY STYLE ANALYSIS
    # =========================================================
    def analyze_play_style(self, recent, owned):
        owned_map = {g["appid"]: g for g in owned}

        total_playtime = sum(g.get("playtime_forever", 0) for g in owned)
        total_recent = sum(g.get("playtime_2weeks", 0) for g in recent)

        focus_ratios = []
        for g in recent:
            appid = g["appid"]
            if appid in owned_map and owned_map[appid]["playtime_forever"] > 0:
                ratio = g.get("playtime_2weeks", 0) / owned_map[appid]["playtime_forever"]
                focus_ratios.append(ratio)

        focus_score = sum(focus_ratios) / len(focus_ratios) if focus_ratios else 0

        return {
            "total_lifetime_hours": round(total_playtime / 60, 1),
            "recent_2weeks_hours": round(total_recent / 60, 1),
            "engagement_trend": "Rising" if total_recent / max(total_playtime, 1) > 0.15 else "Stable",
            "play_style": "Focused" if focus_score > 0.3 else "Diverse",
            "focus_score": round(focus_score, 3)
        }

    # =========================================================
    # DIFFICULTY / INTENSITY INFERENCE
    # =========================================================
    def infer_difficulty_preference(self, df):
        difficulty_signal = (
            df["rating"].fillna(0) *
            df["recent_playtime"]
        ).mean()

        return {
            "difficulty_preference": "Challenging" if difficulty_signal > 5000 else "Relaxed",
            "difficulty_score": round(difficulty_signal, 2)
        }

    # =========================================================
    # TIME × INTENT ALIGNMENT
    # =========================================================
    def infer_time_intent_alignment(self, user_intent, now):
        available = user_intent.get("available_time", 60)

        if available <= 30:
            return "Quick Session"
        elif available <= 90:
            return "Mid-length Play"
        else:
            return "Deep Immersion"

    # =========================================================
    # USER PREFERENCE VECTOR (CORE RECOMMENDATION DATA)
    # =========================================================
    def build_preference_vector(self, df):
        return {
            "genre_weights": df["genres"].explode().value_counts(normalize=True).to_dict(),
            "theme_weights": df["themes"].explode().value_counts(normalize=True).to_dict(),
            "mode_weights": df["modes"].explode().value_counts(normalize=True).to_dict(),
            "rating_affinity": round(df["rating"].mean(), 1),
            "recent_play_bias": round(df["recent_playtime"].mean(), 1)
        }

    # =========================================================
    # MAIN CONTEXT BUILDER
    # =========================================================
    def build_user_context(self, steam_id, user_intent):
        recent = self.get_recent_games(steam_id)
        owned = self.get_owned_games(steam_id)

        if not recent:
            return {"error": "최근 플레이 기록 없음 또는 비공개 계정"}

        records = []
        for game in recent:
            meta = self.get_game_metadata(game["name"])
            records.append({
                "appid": game["appid"],
                "name": game["name"],
                "recent_playtime": game.get("playtime_2weeks", 0),
                "genres": [g["name"] for g in meta.get("genres", [])],
                "themes": [t["name"] for t in meta.get("themes", [])],
                "modes": [m["name"] for m in meta.get("game_modes", [])],
                "rating": meta.get("total_rating", 0)
            })

        df = pd.DataFrame(records)

        # ---------- Aggregations ----------
        genre_counter = Counter(df["genres"].explode())
        theme_counter = Counter(df["themes"].explode())
        mode_counter = Counter(df["modes"].explode())

        avg_recent_hours = round(df["recent_playtime"].mean() / 60, 2)
        now = datetime.now()

        # ---------- Advanced Profiles ----------
        play_style = self.analyze_play_style(recent, owned)
        difficulty_profile = self.infer_difficulty_preference(df)
        time_alignment = self.infer_time_intent_alignment(user_intent, now)
        preference_vector = self.build_preference_vector(df)

        # ---------- FINAL CONTEXT ----------
        return {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_time_context": {
                "day_of_week": now.strftime("%A"),
                "is_weekend": now.weekday() >= 5,
                "time_period": "일과" if 9 <= now.hour < 18 else "저녁/밤"
            },
            "user_behavior_signal": {
                "top_genres": [g for g, _ in genre_counter.most_common(3)],
                "top_themes": [t for t, _ in theme_counter.most_common(3)],
                "preferred_modes": [m for m, _ in mode_counter.most_common(2)],
                "avg_recent_play_hours": avg_recent_hours
            },
            "play_style_profile": play_style,
            "difficulty_profile": difficulty_profile,
            "time_intent_alignment": time_alignment,
            "preference_vector": preference_vector,
            "user_explicit_intent": user_intent,
            "system_constraint": {
                "hardware": user_intent.get("hardware", "Unknown"),
                "cpu": user_intent.get("cpu", "Unknown"),
                "gpu": user_intent.get("gpu", "Unknown"),
                "ram_gb": user_intent.get("ram_gb", 0),
                "free_storage_gb": user_intent.get("free_storage_gb", 0),
                "os": user_intent.get("os", "Unknown"),
                "max_available_time": user_intent.get("available_time")
            }
        }

import os
import requests
import json
import time
from openai import OpenAI

# -----------------------------
# :gear: 환경 변수
# -----------------------------
STEAM_API_KEY = "STEAM_WEB_KEY"
IGDB_CLIENT_ID = "CLIENT_ID"
IGDB_CLIENT_SECRET = "CLIENT_SECRET"
USER_STEAM_ID = "USER_STEAM_ID"
OPENAI_API_KEY = "OPEN_API_KEY"

client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# :one: 유저 입력
# -----------------------------
steam_id = USER_STEAM_ID
user_intent = {
    "available_time": 120,
    "hardware": "PC",
    "cpu": "Intel i7-12700K",
    "gpu": "RTX 4070",
    "ram_gb": 32,
    "free_storage_gb": 500,
    "os": "Windows 11",
    "preferred_genres": ["RPG", "Action"]
}

# -----------------------------
# :two: 유저 컨텍스트 생성
# -----------------------------
pipeline = GameContextPipelineV4(
    steam_api_key=STEAM_API_KEY,
    igdb_client_id=IGDB_CLIENT_ID,
    igdb_client_secret=IGDB_CLIENT_SECRET
)

print(":small_blue_diamond: 유저 컨텍스트 생성 중…")
user_context = pipeline.build_user_context(steam_id, user_intent)

# -----------------------------
# :three: 후보군 게임 가져오기 (Steam API)
# -----------------------------
def get_top_steam_games(limit=200):
    url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    try:
        res = requests.get(url, timeout=5).json()
    except (requests.RequestException, json.JSONDecodeError):
        return []
    apps = res.get("applist", {}).get("apps", [])
    return apps[:limit]

def get_game_details(appid):
    store_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
    try:
        resp = requests.get(store_url, timeout=5)
        resp.raise_for_status()
        data_json = resp.json()
        if not data_json.get(str(appid), {}).get("success"):
            return None
        data = data_json[str(appid)]["data"]
    except (requests.RequestException, json.JSONDecodeError, KeyError):
        return None

    if not data.get("name"):
        return None

    genres = [g["description"] for g in data.get("genres", [])]
    categories = [c["description"] for c in data.get("categories", [])]
    avg_playtime = data.get("playtime_forever", 0)
    difficulty = "Challenging" if "Difficult" in categories else "Moderate"
    mode = "Single player" if "Single-player" in categories else "Multiplayer"
    theme = "Fantasy" if any(t.lower() in data.get("name","").lower() for t in ["dragon","fantasy","magic"]) else None

    return {
        "appid": appid,
        "name": data.get("name"),
        "genres": genres,
        "avg_playtime": avg_playtime,
        "difficulty": difficulty,
        "mode": mode,
        "theme": theme
    }

# -----------------------------
# :four: 후보군 점수 계산
# -----------------------------
def score_game(game, context):
    score = 0
    for g in game["genres"]:
        score += context["preference_vector"]["genre_weights"].get(g,0) * 50
    if game["theme"]:
        score += context["preference_vector"]["theme_weights"].get(game["theme"],0) * 30
    if game["difficulty"] == context["difficulty_profile"]["difficulty_preference"]:
        score += 20
    if game["avg_playtime"] <= context["user_explicit_intent"]["available_time"]*60:
        score += 10
    score *= (1 + context["preference_vector"]["mode_weights"].get(game["mode"],0))
    return score

# -----------------------------
# :five: LLM Reranker
# -----------------------------
def llm_rerank(user_context, candidate_games, top_n=3):
    prompt = f"""
You are a Steam game recommendation expert.

User context:
{json.dumps(user_context, ensure_ascii=False, indent=2)}

Candidate games:
{json.dumps(candidate_games, ensure_ascii=False, indent=2)}

Task:
1. Select the best {top_n} games for this user
2. Rank them
3. Explain why each game fits the user
4. Penalize games that do not fit deep immersion or challenging gameplay
Return JSON with fields: name, score, reason.
"""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role":"user","content":prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content

# -----------------------------
# :six: 추천 파이프라인
# -----------------------------
def recommend_games(top_n=3):
    print(":satellite_antenna: Steam 게임 후보 가져오는 중…")
    apps = get_top_steam_games(limit=100)
    candidates = []
    for i, app in enumerate(apps):
        game = get_game_details(app["appid"])
        if not game or not game["genres"] or not game["name"]:
            continue
        game_score = score_game(game, user_context)
        candidates.append({**game,"score":game_score})
        if i % 20 == 0:
            time.sleep(0.5)  # Steam 과부하 방지

    candidates.sort(key=lambda x:x["score"],reverse=True)
    top_candidates = candidates[:20]  # 후보군 상위 20개

    print(":robot_face: GPT로 최종 랭킹 생성 중…")
    llm_result = llm_rerank(user_context, top_candidates, top_n=top_n)
    print("\n:trophy: 추천 결과:\n", llm_result)
    return llm_result

# -----------------------------
# :seven: 실행
# -----------------------------
if __name__=="__main__":
    recommend_games(top_n=3) 