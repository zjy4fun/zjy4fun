import json
import os
import datetime as dt
from typing import Any, Dict, List

import requests

API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
ORG_ID = os.environ.get("OPENAI_ORG_ID", "").strip()
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "30"))
MODEL_KEYWORD = os.environ.get("CODEX_MODEL_KEYWORD", "codex").lower().strip()

if not API_KEY:
    raise SystemExit("OPENAI_API_KEY is required")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
if ORG_ID:
    headers["OpenAI-Organization"] = ORG_ID

end = dt.datetime.now(dt.timezone.utc)
start = end - dt.timedelta(days=LOOKBACK_DAYS)

params = {
    "start_time": int(start.timestamp()),
    "end_time": int(end.timestamp()),
    "limit": 1000,
}


def request_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.get(url, headers=headers, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_data() -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    usage_url = "https://api.openai.com/v1/organization/usage/completions"
    costs_url = "https://api.openai.com/v1/organization/costs"

    usage = request_json(usage_url, params)
    costs = request_json(costs_url, params)
    return usage.get("data", []), costs.get("data", [])


def pick_model_name(item: Dict[str, Any]) -> str:
    for k in ("model", "model_name"):
        v = item.get(k)
        if isinstance(v, str):
            return v.lower()
    return ""


def to_int(item: Dict[str, Any], *keys: str) -> int:
    for k in keys:
        v = item.get(k)
        if v is None:
            continue
        try:
            return int(v)
        except Exception:
            pass
    return 0


def to_float(item: Dict[str, Any], *keys: str) -> float:
    for k in keys:
        v = item.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except Exception:
            pass
    return 0.0


def summarize(usage_items: List[Dict[str, Any]], cost_items: List[Dict[str, Any]]) -> tuple[int, float]:
    total_tokens = 0
    for it in usage_items:
        model = pick_model_name(it)
        if MODEL_KEYWORD not in model:
            continue
        total_tokens += to_int(it, "input_tokens")
        total_tokens += to_int(it, "output_tokens")
        total_tokens += to_int(it, "input_cached_tokens")

    total_cost = 0.0
    for it in cost_items:
        model = pick_model_name(it)
        if MODEL_KEYWORD and MODEL_KEYWORD not in model:
            continue
        total_cost += to_float(it, "amount", "cost", "usd")

    return total_tokens, total_cost


def write_badge_json(tokens: int, cost: float) -> None:
    os.makedirs("badges", exist_ok=True)
    message = f"{tokens:,} tokens / ${cost:.2f} ({LOOKBACK_DAYS}d)"
    payload = {
        "schemaVersion": 1,
        "label": "codex usage",
        "message": message,
        "color": "5c7cfa",
    }
    with open("badges/codex-usage.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    try:
        usage_items, cost_items = fetch_data()
        tokens, cost = summarize(usage_items, cost_items)
        write_badge_json(tokens, cost)
        print(f"Updated badge: tokens={tokens}, cost=${cost:.2f}")
    except Exception as e:
        # Fail-safe: keep workflow green with explicit status badge message
        os.makedirs("badges", exist_ok=True)
        payload = {
            "schemaVersion": 1,
            "label": "codex usage",
            "message": f"update failed: {str(e)[:50]}",
            "color": "red",
        }
        with open("badges/codex-usage.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        raise


if __name__ == "__main__":
    main()
