import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Union

import cmd2
from json_manager.buffered_cmd2 import BufferedCmd  # Or however you import it
import requests  # For downloading JSON from a URL
from thefuzz import fuzz  # For fuzzy matching score
from dotenv import load_dotenv  # For loading environment variables from .env

CMD_CATEGORY = "JSON Manager"


def get_nested_value(record: Dict[str, Any], field_path: str) -> Optional[Any]:
    """
    Retrieve a nested value from a dictionary given a dot-separated field path.
    For example, get_nested_value(record, "int.hello") returns record["int"]["hello"] if it exists.
    """
    parts = field_path.split(".")
    current = record
    for part in parts:
        if not isinstance(current, dict):
            return None
        if part not in current:
            return None
        current = current[part]
    return current


class Console(BufferedCmd):
    CMD_CATEGORY = CMD_CATEGORY

    def __init__(self, *args, **kwargs) -> None:
        # Load environment variables from a .env file
        load_dotenv()
        super().__init__(*args, **kwargs)

        self.prompt = "JSON CLI> "
        self.intro = cmd2.style("Welcome to json-manager CLI", fg=cmd2.Fg.GREEN, bold=True)

        # Example settable value (for demonstration)
        self.settable_value: int = 12
        self.add_settable(cmd2.Settable("settable_value", str, "Settable value description", self))

        # self.data can be either a dict or a list (or None if nothing loaded)
        self.data: Optional[Union[Dict[str, Any], List[Any]]] = None
        self.file_path: Optional[str] = None

    def ensure_data_loaded(self) -> bool:
        """
        Ensure that self.data is loaded. If not, print an error and return False.
        """
        if self.data is None:
            self.perror("No data loaded. Please use 'load <path_or_url>' first.")
            return False
        return True

    def save_data(self) -> None:
        """
        Write (sync) the in-memory data back to disk in JSON format.
        Called at the end of every command to ensure changes are always persisted.
        """
        if self.file_path and self.data is not None:
            try:
                with open(self.file_path, "w", encoding="utf-8", errors="replace") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                self.perror(f"Error writing data to {self.file_path}: {e}")

    def load_json(self, source: str) -> None:
        """
        Load JSON data from a local file or a URL into self.data "as is".
          - If the data is a dict, we keep it as a dict.
          - If it's a list, we keep it as a list.
          - Otherwise, we error out.

        The loaded data is synced to disk under 'self.file_path'.
        """
        data: Union[List[Any], Dict[str, Any]] = []
        previous_file_path = self.file_path

        # 1) Handle remote URLs
        if source.startswith("http://") or source.startswith("https://"):
            try:
                response = requests.get(source)
                response.raise_for_status()
                data = response.json()
                # We’ll store the downloaded data into "downloaded.json"
                self.file_path = "downloaded.json"
            except Exception as e:
                self.perror(f"Error downloading JSON: {e}")
                self.file_path = previous_file_path
                return
        # 2) Otherwise treat `source` as a local file path
        else:
            self.file_path = source
            try:
                with open(source, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
            except Exception as e:
                self.perror(f"Error reading JSON file: {e}")
                self.file_path = previous_file_path
                return

        # 3) Accept dict or list; otherwise, reject
        if not isinstance(data, (dict, list)):
            self.perror("Unsupported JSON format (must be a dict or a list).")
            self.file_path = previous_file_path
            return

        self.data = data
        self.poutput("JSON data loaded successfully.")
        self.save_data()  # Always sync after loading

    load_parser = cmd2.Cmd2ArgumentParser()
    load_parser.add_argument("source", help="Local file path or URL of the JSON file")

    @cmd2.with_argparser(load_parser)
    @cmd2.with_category(CMD_CATEGORY)
    def do_load(self, args: Any) -> None:
        """
        Load a JSON file from a local path or URL.

        Usage: load <source>
        """
        self.load_json(args.source.strip())
        self.save_data()  # Always sync

    insert_parser = cmd2.Cmd2ArgumentParser()
    insert_parser.add_argument("record", help="JSON string representing the record to insert")

    @cmd2.with_argparser(insert_parser)
    @cmd2.with_category(CMD_CATEGORY)
    def do_insert(self, args: Any) -> None:
        """
        Insert a new record (a dictionary) into the loaded JSON if it's a list.
        If the loaded JSON is a dict, insertion is not permitted.

        Usage: insert <json_record>
        Example: insert '{"name": "Alice", "age": 30}'
        """
        if not self.ensure_data_loaded():
            self.save_data()
            return

        try:
            record = json.loads(args.record)
            if not isinstance(record, dict):
                self.perror("Insert expects a JSON object (dictionary).")
                self.save_data()
                return

            if isinstance(self.data, list):
                self.data.append(record)
                self.poutput("Record inserted successfully.")
            else:
                self.perror("Current data is a dictionary (not a list). Cannot insert.")
        except json.JSONDecodeError:
            self.perror("Invalid JSON record provided.")
        except Exception as e:
            self.perror(f"Error inserting record: {e}")
        finally:
            self.save_data()  # Always sync after command

    # ---------------------------
    # SEARCH COMMAND (Exact Match)
    # ---------------------------
    search_parser = cmd2.Cmd2ArgumentParser()
    search_parser.add_argument("value", help="Value to search for (exact match)")
    search_parser.add_argument(
        "--field",
        action="append",
        required=True,
        help="Field(s) to search in. Use dot notation for nested fields (e.g. int.hello)."
    )

    @cmd2.with_argparser(search_parser)
    @cmd2.with_category(CMD_CATEGORY)
    def do_search(self, args: Any) -> None:
        """
        Search for records (dicts) where any of the specified fields exactly equal the given value.
        - If data is a list, we search among all list elements that are dicts.
        - If data is a dict, we search that single dict.

        Usage: search <value> --field <field1> [--field <field2> ...]
        """
        if not self.ensure_data_loaded():
            self.save_data()
            return

        results_found = False

        if isinstance(self.data, dict):
            # Treat self.data as one "record"
            record = self.data
            for field in args.field:
                field_val = get_nested_value(record, field)
                if field_val is not None and str(field_val) == args.value:
                    self.poutput(f"Match found in field '{field}':")
                    self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
                    results_found = True
                    break

        elif isinstance(self.data, list):
            for idx, item in enumerate(self.data, start=1):
                if not isinstance(item, dict):
                    continue
                for field in args.field:
                    field_val = get_nested_value(item, field)
                    if field_val is not None and str(field_val) == args.value:
                        self.poutput(f"Match found in item #{idx}, field '{field}':")
                        self.poutput(json.dumps(item, indent=4, ensure_ascii=False))
                        results_found = True
                        break

        if not results_found:
            self.poutput("No matching records found.")

        self.save_data()  # Always sync

    # ---------------------------
    # FUZZY SEARCH COMMAND
    # ---------------------------
    fuzzy_parser = cmd2.Cmd2ArgumentParser()
    fuzzy_parser.add_argument(
        "search_term",
        help="Term to fuzzy search for"
    )
    fuzzy_parser.add_argument(
        "--field",
        action="append",
        required=True,
        help="Field(s) to perform fuzzy search on. Use dot notation for nested fields (e.g. int.hello)."
    )
    fuzzy_parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Minimum fuzzy match score to consider a match (default: 80)"
    )

    @cmd2.with_argparser(fuzzy_parser)
    def do_fuzzy_search(self, args):
        """
        Perform a fuzzy search on records (dicts) using the specified field(s).
        - If data is a list, we search among all list elements that are dicts.
        - If data is a dict, we treat it as a single "record."
        If the fuzzy match score >= threshold, we collect the match and sort by score DESC.
        """
        if not self.ensure_data_loaded():
            self.save_data()
            return

        threshold = args.threshold
        results = []  # we will store (score, index, record_dict, field, field_value)

        if isinstance(self.data, dict):
            # Single dictionary case
            record = self.data
            for field in args.field:
                field_val = get_nested_value(record, field)
                if field_val is not None:
                    score = fuzz.ratio(args.search_term, str(field_val))
                    if score >= threshold:
                        # store in results
                        results.append((score, 1, record, field, field_val))

        elif isinstance(self.data, list):
            # List of items
            for idx, item in enumerate(self.data, start=1):
                if not isinstance(item, dict):
                    continue
                for field in args.field:
                    field_val = get_nested_value(item, field)
                    if field_val is not None:
                        score = fuzz.ratio(args.search_term, str(field_val))
                        if score >= threshold:
                            results.append((score, idx, item, field, field_val))
                            # break if you only want first match per item
                            # otherwise, keep checking other fields

        # Sort results by score descending
        results.sort(key=lambda x: x[0], reverse=True)

        if not results:
            self.poutput("No fuzzy matching records found.")
        else:
            for score, idx, record, field, field_val in results:
                if isinstance(self.data, dict):
                    # single record case
                    self.poutput(
                        f"Fuzzy match (score={score}, field='{field}' -> '{field_val}'):"
                    )
                    self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
                else:
                    # list case
                    self.poutput(
                        f"Fuzzy match in item #{idx} (score={score}, field='{field}' -> '{field_val}'):"
                    )
                    self.poutput(json.dumps(record, indent=4, ensure_ascii=False))

        self.save_data()  # Always sync

    @cmd2.with_category(CMD_CATEGORY)
    def do_open_json(self, args: Any) -> None:
        """
        Open the currently loaded JSON file using the default editor specified in the EDITOR environment variable.

        Usage: open_json
        """
        if not self.file_path or not os.path.exists(self.file_path):
            self.perror("No JSON file loaded. Please load a JSON file first.")
            self.save_data()
            return

        editor = os.getenv("EDITOR")
        if not editor:
            self.perror("Environment variable EDITOR is not set. Please set it to your preferred text editor.")
            self.save_data()
            return

        try:
            subprocess.run([editor, self.file_path])
        except Exception as e:
            self.perror(f"Error opening JSON file: {e}")

        self.save_data()  # Always sync

    @cmd2.with_category(CMD_CATEGORY)
    def do_status(self, args: Any) -> None:
        """
        Display the current system status including loaded file and data information.

        Usage: status
        """
        status_info = []
        if self.file_path:
            status_info.append(f"Loaded file: {self.file_path}")
        else:
            status_info.append("No file loaded.")

        if self.data is None:
            status_info.append("No data loaded.")
        else:
            if isinstance(self.data, dict):
                status_info.append("Data is a single dictionary.")
            elif isinstance(self.data, list):
                status_info.append(f"Data is a list with {len(self.data)} item(s).")

        for line in status_info:
            self.poutput(line)

        self.save_data()  # Always sync

def main() -> None:
    """
    Instantiate and run the Console CLI app.
    Optionally load a JSON file at startup if the --json argument is provided.
    """
    import sys
    import argparse

    # Reconfigure stdout for Unicode handling if possible
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="json-manager CLI")
    parser.add_argument(
        "--json",
        type=str,
        help="Path or URL to a JSON file to load at startup",
        default=None,
    )
    args, unknown = parser.parse_known_args()

    # Remove extra arguments so cmd2 doesn't complain.
    sys.argv = [sys.argv[0]]

    c = Console()
    if args.json:
        c.load_json(args.json)
        c.save_data()
    c.cmdloop()


if __name__ == "__main__":
    main()
