#!/usr/bin/env python3
import argparse
import os
import sys
import json
from urllib.parse import urlparse
import requests

TEMP_DIR = "temp/"

def download_json(url: str, temp_dir: str=TEMP_DIR) -> str:
    """
    Download JSON from a URL into the temporary directory.
    Uses the last part of the URL path as the filename,
    appending ".json" if not already present.
    """
    os.makedirs(temp_dir, exist_ok=True)
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename.endswith(".json"):
        filename += ".json"
    file_path = os.path.join(temp_dir, filename)
    print(f"Downloading JSON from {url} to {file_path}...")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return file_path

def is_tinydb_format(data: any) -> bool:
    """
    Check if the JSON data is TinyDB-compatible.
    That is, if it is a dict with a '_default' key whose value is a dict.
    """
    return isinstance(data, dict) and "_default" in data and isinstance(data["_default"], dict)

def main():
    parser = argparse.ArgumentParser(description="Console Picker/Selector for json-manager")
    parser.add_argument("json", help="Path or URL to the JSON file")
    parser.add_argument("--temp", type=str, default="temp/", help="Temporary directory for downloaded JSON files")
    args = parser.parse_args()

    file_path = args.json

    # If args.json is a URL, download the file to the temp directory.
    if args.json.startswith("http://") or args.json.startswith("https://"):
        try:
            file_path = download_json(args.json, args.temp)
            print(f"JSON file downloaded to: {file_path}")
        except Exception as e:
            print(f"Error downloading JSON: {e}")
            sys.exit(1)

    # Load the JSON file to inspect its structure.
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)

    # If the JSON is TinyDB-compatible (has '_default') or is a list, use db_console.
    if is_tinydb_format(data) or isinstance(data, list):
        print("Launching db_console...")
        # Pass the file as an argument to db_console by resetting sys.argv
        sys.argv = [sys.argv[0], "--json", file_path]
        from json_manager import db_console
        db_console.main()
    else:
        print("Launching json_console...")
        sys.argv = [sys.argv[0], "--json", file_path]
        from json_manager import json_console
        json_console.main()

if __name__ == "__main__":
    main()
