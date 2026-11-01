"""Run from the project root: python -m scripts.prepare_data."""

import json

from src.data.preparation import prepare_data

if __name__ == "__main__":
    report = prepare_data()
    print(json.dumps({k: v for k, v in report.items() if k != "sources"}, ensure_ascii=False, indent=2))

