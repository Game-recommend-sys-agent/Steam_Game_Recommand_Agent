"""
context_bundle 조립기

목표:
- (5) user_behavior(processed) + (6~8) game_bundles(processed)를 합쳐
  `docs/context_aware.md`의 ContextBundle 형태에 가까운 JSON을 만든다.

주의:
- 이 모듈은 "조립(merge)"에 집중한다. (6~8) 번들 생성/갱신(TTL)은 별도 스크립트가 담당.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.game_recommendation.context_aware.behavior_activity import (
    UserBehaviorPaths,
    processed_behavior_context_path,
)
from src.game_recommendation.context_aware.game_signals import (
    GameSignalsPaths,
    processed_bundle_path,
)


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def _safe_int(x: Any, default: int = 0) -> int:
    if x is None:
        return default
    try:
        return int(x)
    except (ValueError, TypeError):
        return default


@dataclass(frozen=True)
class ContextBundlePaths:
    """
    서로 다른 모듈의 paths를 한 번에 전달하기 위한 wrapper.
    """

    user: UserBehaviorPaths = UserBehaviorPaths()
    game: GameSignalsPaths = GameSignalsPaths()
    processed_dir: Path = Path("data/processed")


def context_bundle_output_path(
    steam_id: str, *, paths: ContextBundlePaths, cc: str = "us", lang: str = "en"
) -> Path:
    return paths.processed_dir / "context_bundles" / f"{steam_id}__cc={cc}__lang={lang}.json"


def load_behavior_processed(steam_id: str, *, paths: ContextBundlePaths) -> dict[str, Any]:
    """
    (5) processed BehaviorContext를 로드한다.
    - data/processed/user_behavior/{steam_id}.json
    """
    p = processed_behavior_context_path(steam_id, paths=paths.user)
    return _read_json(p)


def load_game_bundle_processed(
    appid: int, *, paths: ContextBundlePaths, cc: str = "us", lang: str = "en"
) -> dict[str, Any]:
    """
    (6~8) processed game bundle을 로드한다.
    - data/processed/game_bundles/{appid}__cc={cc}__lang={lang}.json
    """
    p = processed_bundle_path(appid, paths=paths.game, cc=cc, lang=lang)
    return _read_json(p)


def assemble_context_bundle(
    *,
    steam_id: str,
    appids: list[int],
    paths: ContextBundlePaths,
    cc: str = "us",
    lang: str = "en",
    now_ts: int | None = None,
    include_game_bundle_meta: bool = True,
) -> dict[str, Any]:
    """
    ContextBundle을 조립한다.

    games는 JSON 특성상 키가 문자열이므로 appid를 str로 사용한다.
    """
    now_ts = int(now_ts or time.time())

    behavior_payload = load_behavior_processed(steam_id, paths=paths)
    behavior_ctx = (
        behavior_payload.get("behavior", {})
        if isinstance(behavior_payload, dict)
        else {}
    )

    missing_appids: list[int] = []
    stale_appids: list[int] = []
    games_out: dict[str, Any] = {}

    for appid in appids:
        if not isinstance(appid, int) or appid <= 0:
            continue
        try:
            bundle = load_game_bundle_processed(appid, paths=paths, cc=cc, lang=lang)
        except FileNotFoundError:
            missing_appids.append(appid)
            continue

        contexts = bundle.get("contexts", {}) if isinstance(bundle, dict) else {}
        meta = bundle.get("meta", {}) if isinstance(bundle, dict) else {}

        expires_at = _safe_int(meta.get("expires_at"), 0)
        if expires_at > 0 and expires_at <= now_ts:
            stale_appids.append(appid)

        entry: dict[str, Any] = {
            # docs/context_aware.md GameContext에 맞춰 key를 평평하게 둔다.
            "quality_trust": contexts.get("quality_trust"),
            "live": contexts.get("live"),
            "discount": contexts.get("discount"),
        }
        if include_game_bundle_meta:
            entry["_bundle_meta"] = meta
        games_out[str(appid)] = entry

    return {
        "meta": {
            "steam_id": steam_id,
            "generated_at": now_ts,
            "cc": cc,
            "lang": lang,
            "requested_appids": [int(a) for a in appids if isinstance(a, int) and a > 0],
            "missing_appids": missing_appids,
            "stale_appids": stale_appids,
        },
        "user_id": steam_id,  # docs/context_aware.md의 user_id 관례를 따름
        "user": {
            "behavior": behavior_ctx,
        },
        "games": games_out,
    }


def validate_context_bundle(bundle: dict[str, Any]) -> list[str]:
    """
    간단한 상식 범위/결측/TTL 이슈를 문자열 리스트로 반환한다.
    (샘플 스냅샷 검증용)
    """
    issues: list[str] = []
    if not isinstance(bundle, dict):
        return ["bundle is not a dict"]

    meta = bundle.get("meta", {})
    now_ts = _safe_int(meta.get("generated_at"), 0)
    missing = meta.get("missing_appids")
    stale = meta.get("stale_appids")
    if isinstance(missing, list) and missing:
        issues.append(f"missing_appids: {missing}")
    if isinstance(stale, list) and stale:
        issues.append(f"stale_appids(expired bundles): {stale}")

    user = bundle.get("user", {})
    behavior = user.get("behavior") if isinstance(user, dict) else None
    if not isinstance(behavior, dict):
        issues.append("user.behavior missing or not a dict")
    else:
        st = behavior.get("activity_state")
        if st not in ("active", "cooling_off", "dormant"):
            issues.append(f"behavior.activity_state invalid: {st!r}")

    games = bundle.get("games", {})
    if not isinstance(games, dict):
        issues.append("games missing or not a dict")
        return issues
    if not games and isinstance(meta.get("requested_appids"), list) and meta.get("requested_appids"):
        issues.append("requested_appids not empty but games is empty (all missing?)")

    for appid_str, gctx in games.items():
        if not isinstance(gctx, dict):
            issues.append(f"games[{appid_str}] not a dict")
            continue

        # TTL(선택): _bundle_meta가 있으면 검사
        bm = gctx.get("_bundle_meta")
        if isinstance(bm, dict):
            expires_at = _safe_int(bm.get("expires_at"), 0)
            if expires_at > 0 and now_ts > 0 and expires_at <= now_ts:
                issues.append(f"games[{appid_str}] bundle expired (expires_at={expires_at})")

        qt = gctx.get("quality_trust")
        if isinstance(qt, dict):
            for k in ("review_positive_ratio", "confidence", "quality_trust_score"):
                v = qt.get(k)
                if isinstance(v, (int, float)) and not (0.0 <= float(v) <= 1.0):
                    issues.append(f"games[{appid_str}].quality_trust.{k} out of [0,1]: {v}")

        live = gctx.get("live")
        if isinstance(live, dict):
            v = live.get("liveness_signal")
            if isinstance(v, (int, float)) and not (0.0 <= float(v) <= 1.0):
                issues.append(f"games[{appid_str}].live.liveness_signal out of [0,1]: {v}")

        disc = gctx.get("discount")
        if isinstance(disc, dict):
            dp = disc.get("discount_percent")
            if isinstance(dp, int) and not (0 <= dp <= 100):
                issues.append(f"games[{appid_str}].discount.discount_percent out of [0,100]: {dp}")
            ds = disc.get("discount_signal")
            if isinstance(ds, (int, float)) and not (0.0 <= float(ds) <= 1.0):
                issues.append(f"games[{appid_str}].discount.discount_signal out of [0,1]: {ds}")

    return issues


def write_context_bundle(
    bundle: dict[str, Any], *, steam_id: str, paths: ContextBundlePaths, cc: str = "us", lang: str = "en"
) -> Path:
    out = context_bundle_output_path(steam_id, paths=paths, cc=cc, lang=lang)
    _atomic_write_json(out, bundle)
    return out

