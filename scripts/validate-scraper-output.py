#!/usr/bin/env python3
import json
import os
import sys


DATA_PATH = "data/scraper.json"
STATIC_DATA_PATH = "static/data.json"
IMG_DIR = "static/img"
SECTIONS = ("movies", "shows", "books", "spotify", "github", "videogames")


def main():
    data = load_json(DATA_PATH)
    static_data = load_json(STATIC_DATA_PATH)
    errors = []

    if data != static_data:
        errors.append(f"{DATA_PATH} and {STATIC_DATA_PATH} differ")

    for section in SECTIONS:
        if section not in data:
            errors.append(f"missing section: {section}")
        elif not isinstance(data[section], list):
            errors.append(f"section is not a list: {section}")

    for section, items in data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            title = item.get("title") or item.get("name") or "<unknown>"
            for key in ("img", "img_webp"):
                filename = item.get(key)
                if filename:
                    validate_image(section, title, filename, errors)

    if errors:
        print("Scraper output validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Scraper output validation passed.")
    return 0


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"Failed to read {path}: {exc}")
        sys.exit(1)


def validate_image(section, title, filename, errors):
    path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(path):
        errors.append(f"missing image: {filename} ({section}: {title})")
        return
    if os.path.getsize(path) == 0:
        errors.append(f"zero-byte image: {filename} ({section}: {title})")


if __name__ == "__main__":
    sys.exit(main())
