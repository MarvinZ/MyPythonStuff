import json
import sys
from pathlib import Path

SRC = "Source2.json"
OUT = "result2.json"

def main():
    try:
        raw = Path(SRC).read_text(encoding="utf-8")
    except FileNotFoundError:
        print("Error: Source2.json not found")
        sys.exit(1)

    try:
        outer = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error parsing outer JSON: {e}")
        sys.exit(1)

    answer = outer.get("answer")
    if isinstance(answer, str):
        try:
            parsed_answer = json.loads(answer)
            outer["answer"] = parsed_answer
        except json.JSONDecodeError as e:
            print(f"Error parsing answer JSON: {e}")
            sys.exit(1)

    Path(OUT).write_text(
        json.dumps(outer, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"OK -> {OUT}")

if __name__ == "__main__":
    main()
