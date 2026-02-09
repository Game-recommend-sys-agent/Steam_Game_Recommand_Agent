# contexts/play_style.py
from typing import List, Dict


def build(play_log: List[Dict]) -> Dict:
    """
    play_log: List of games with playtime info
      [
        {
          "appid": int,
          "playtime_forever": int,      # minutes
          "playtime_2weeks": int        # minutes
        },
        ...
      ]
    """

    if not play_log:
        return {
            "avg_lifetime_hours": 0.0,
            "focus_score": 0.0,
            "play_style": "Unknown",
            "difficulty_pref": "Unknown"
        }

    # ① 평균 누적 플레이 시간 (시간 단위)
    total_playtime = sum(g["playtime_forever"] for g in play_log)
    avg_lifetime_hours = round((total_playtime / len(play_log)) / 60, 2)

    # ② 집중도 점수 (Focus Score)
    ratios = [
        g["playtime_2weeks"] / g["playtime_forever"]
        for g in play_log
        if g["playtime_forever"] > 0
    ]
    focus_score = round(sum(ratios) / len(ratios), 2) if ratios else 0.0

    # ③ 플레이 스타일 분류
    play_style = "Focused" if focus_score > 0.3 else "Diverse"

    # ④ 난이도 선호 추정
    recent_playtime = sum(g["playtime_2weeks"] for g in play_log)
    difficulty_pref = (
        "Challenging"
        if total_playtime > 0 and (recent_playtime / total_playtime) > 0.2
        else "Relaxed"
    )

    return {
        "avg_lifetime_hours": avg_lifetime_hours,
        "focus_score": focus_score,
        "play_style": play_style,
        "difficulty_pref": difficulty_pref
    }