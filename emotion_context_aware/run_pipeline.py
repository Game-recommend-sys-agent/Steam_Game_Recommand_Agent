import json
from dotenv import load_dotenv
load_dotenv()

from steam_collect import (
    collect_game_narrative_inputs,
    build_llm_payload
)
from emotional_inference import LLM_emotional_inference
from openai import OpenAI

client = OpenAI()

GAME_APPID = "1641960"

raw = collect_game_narrative_inputs(GAME_APPID)
payload = build_llm_payload(raw)

emotion_schema = LLM_emotional_inference(payload, client)

print(json.dumps(emotion_schema, indent=2, ensure_ascii=False))