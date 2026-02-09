# contexts/situational.py
from datetime import datetime
from typing import Dict, List


def infer_time_of_day(hour: int) -> str:
    if 0 <= hour < 6:
        return "late_night"
    elif 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"


def infer_avg_session_duration(recent_playtimes: List[int]) -> int:
    """
    recent_playtimes: list of playtime_2weeks per game (minutes)
    """
    if not recent_playtimes:
        return 60  # fallback for cold start
    return sum(recent_playtimes) // len(recent_playtimes)


def infer_commitment(last_played_gap_minutes: int) -> str:
    """
    How recently the user played any game.
    """
    if last_played_gap_minutes > 1440:  # more than 1 day
        return "low_commitment"
    return "high_commitment"


def infer_session_fit(
    available_time: int,
    avg_session_duration: int
) -> str:
    """
    Decide whether current session should be short or long.
    """
    if available_time <= 45 or available_time < avg_session_duration:
        return "short"
    return "long"


def build(user_input: Dict, time_input: Dict | None = None) -> Dict:
    """
    Build situational context.

    user_input:
      - available_time_window (minutes)
      - recent_playtime_2weeks (list[int])
      - last_played_gap_minutes (int)

    time_input:
      - datetime (ISO string or datetime object)
    """

    available_time = user_input["available_time_window"]
    recent_playtimes = user_input.get("recent_playtime_2weeks", [])
    last_played_gap = user_input.get("last_played_gap_minutes", 9999)

    avg_session_duration = infer_avg_session_duration(recent_playtimes)

    if time_input and "datetime" in time_input:
        now = (
            time_input["datetime"]
            if isinstance(time_input["datetime"], datetime)
            else datetime.fromisoformat(time_input["datetime"])
        )
    else:
        now = datetime.now()

    time_of_day = infer_time_of_day(now.hour)
    is_weekend = now.weekday() >= 5

    session_fit = infer_session_fit(
        available_time,
        avg_session_duration
    )

    commitment = infer_commitment(last_played_gap)

    situational_tags = [
        time_of_day,
        f"{session_fit}_session",
        commitment
    ]

    return {
        "available_time_window": available_time,
        "average_session_duration": avg_session_duration,
        "time_of_day": time_of_day,
        "is_weekend": is_weekend,
        "session_fit": session_fit,
        "commitment": commitment,
        "situational_tags": situational_tags
    }