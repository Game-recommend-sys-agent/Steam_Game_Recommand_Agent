# filters/filters.py

# ==================================================
# Stage 1 : OS Filter (CSV 기반)  ✅ OS만
# ==================================================
def filter_os(games_df, user_os: str):
    col_map = {
        "windows": "Windows",
        "mac": "Mac",
        "linux": "Linux",
    }

    col = col_map.get(user_os)
    if col is None or col not in games_df.columns:
        return games_df

    return games_df[games_df[col].astype(bool)]


# ==================================================
# Stage 2 : Age Filter (API required_age)
# ==================================================
def filter_age(parsed_app: dict, user_age_limit: int) -> bool:
    required_age = parsed_app.get("required_age")

    if required_age is None:
        return True

    # 🔥 핵심: 타입 정규화
    try:
        required_age = int(required_age)
    except (ValueError, TypeError):
        return True  # 파싱 불가 → 보수적으로 통과

    return required_age <= user_age_limit

# ==================================================
# Stage 2 : Genre Filter (API + 그룹화, 확장판)
# ==================================================
GENRE_GROUP_MAP = {
    # 🎯 액션
    "action": "action",
    "shooter": "action",
    "platform": "action",
    "fighting": "action",
    "hack": "action",
    "slash": "action",
    "battle": "action",

    # 🧙 RPG
    "rpg": "rpg",
    "jrpg": "rpg",
    "crpg": "rpg",
    "mmorpg": "rpg",
    "role-playing": "rpg",

    # 🧠 전략
    "strategy": "strategy",
    "turn-based": "strategy",
    "real-time": "strategy",
    "4x": "strategy",
    "tower defense": "strategy",
    "auto battler": "strategy",

    # 🌿 시뮬레이션
    "simulation": "simulation",
    "sim": "simulation",
    "sandbox": "simulation",
    "builder": "simulation",
    "farming": "simulation",
    "city": "simulation",

    # 📖 스토리 중심
    "visual novel": "story",
    "interactive fiction": "story",
    "dating": "story",
    "walking simulator": "story",
    "point & click": "story",

    # 🧩 퍼즐 / 캐주얼
    "puzzle": "casual",
    "casual": "casual",
    "word": "casual",
    "rhythm": "casual",
    "arcade": "casual",
    "card": "casual",
    "board": "casual",
    "tabletop": "casual",

    # 🌐 온라인 / 경쟁
    "moba": "online",
    "esports": "online",
    "pvp": "online",
    "multiplayer": "online",

    # 🎨 제작 / 툴
    "design": "tool",
    "animation": "tool",
    "modeling": "tool",
    "video": "tool",
    "audio": "tool",
    "utility": "tool",
}


def filter_genre(parsed_app: dict, selected_groups: list[str]) -> bool:
    genres = parsed_app.get("genres")
    if not genres or not genres.get("all_genres"):
        return True  # 정보 없으면 보수적 통과

    game_groups = set()

    for g in genres["all_genres"]:
        g_lower = g.lower()

        for key, group in GENRE_GROUP_MAP.items():
            if key in g_lower:
                game_groups.add(group)

    if not game_groups:
        return True  # 매핑 실패 시 탈락시키지 않음

    return any(group in game_groups for group in selected_groups)


# ==================================================
# Stage 2 : Price Filter
# ==================================================
def filter_price(parsed_app: dict, price_bucket: str) -> bool:
    price = parsed_app.get("final_price")
    if price is None:
        return True

    if price_bucket == "lt_10000":
        return price < 10000
    if price_bucket == "10000_30000":
        return 10000 <= price < 30000
    if price_bucket == "30000_50000":
        return 30000 <= price < 50000
    if price_bucket == "gte_50000":
        return price >= 50000

    return True


# ==================================================
# Stage 2 : Discount Filter
# ==================================================
# def filter_discount(parsed_app: dict, discount_buckets: list[str]) -> bool:
#     # 상관없음이면 통과
#     if not discount_buckets or "any" in discount_buckets:
#         return True

#     discount = parsed_app.get("discount_percent")

#     # 🔥 핵심: 할인 정보 없거나 0이면 '할인 아님'
#     if discount is None or discount == 0:
#         return False

#     for bucket in discount_buckets:
#         if bucket == "gte_90" and discount >= 90:
#             return True
#         if bucket == "70_90" and 70 <= discount < 90:
#             return True
#         if bucket == "50_70" and 50 <= discount < 70:
#             return True
#         if bucket == "30_50" and 30 <= discount < 50:
#             return True
#         if bucket == "lt_30" and discount < 30:
#             return True

#     return False
# ==================================================
# Stage 2 : Spec Filter
# ==================================================
def filter_spec(parsed_app: dict, spec_preset: str) -> bool:
    ram = parsed_app.get("pc_spec", {}).get("min_ram_gb")
    if ram is None:
        return True

    limits = {
        "low": 8,
        "mid": 12,
        "high": float("inf"),
    }

    return ram <= limits[spec_preset]