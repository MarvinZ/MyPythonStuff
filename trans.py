import json
import re
import sys
from pathlib import Path

SRC = "Source.json"
OUT = "result.json"
MARK = "<JSONQuotes>"

def main():
    try:
        raw = Path(SRC).read_text(encoding="utf-8")
    except FileNotFoundError:
        print("Error: Source.json not found")
        sys.exit(1)

    try:
        outer = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error parsing outer JSON: {e}")
        sys.exit(1)

    prompt = outer.get("prompt")
    if not isinstance(prompt, str):
        print("Error: prompt is not a string")
        sys.exit(1)

    m = re.search(rf"{re.escape(MARK)}\s*({{.*}})", prompt, re.DOTALL)
    if not m:
        print("Error: <JSONQuotes> block not found in prompt")
        sys.exit(1)

    payload = m.group(1)
    if payload.startswith("{{"):
        payload = payload[1:]

    try:
        quotes_obj = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"Error parsing embedded JSON: {e}")
        sys.exit(1)

    instruction_text = prompt[: m.start()].strip()

    outer["prompt"] = {
        "text": instruction_text,
        "JSONQuotes": quotes_obj
    }

    Path(OUT).write_text(
        json.dumps(outer, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"OK -> {OUT}")

if __name__ == "__main__":
    main()
