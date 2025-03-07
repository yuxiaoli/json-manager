import json
import os
import subprocess
from typing import Any, Dict, List, Optional

import cmd2
from json_manager.buffered_cmd2 import BufferedCmd  # Updated import
import requests  # For downloading JSON from a URL
from tinydb import TinyDB, Query  # For database operations
from tinydb.storages import JSONStorage
# from tinydb.storages import MemoryStorage
# from tinydb.middlewares import CachingMiddleware
from thefuzz import fuzz  # For fuzzy matching score
from dotenv import load_dotenv  # For loading environment variables from .env

from json_manager.main import download_json

CMD_CATEGORY = "JSON Manager"


class UTF8ReplaceJSONStorage(JSONStorage):
    """
    Custom TinyDB storage that forces UTF-8 reading with error replacement.
    """
    def read(self) -> Any:
        try:
            with open(self._handle.name, 'r', encoding='utf-8', errors='replace') as fh:
                return json.load(fh)
        except FileNotFoundError:
            return None


def get_nested_value(record: Dict[str, Any], field_path: str) -> Optional[Any]:
    """
    Retrieve a nested value from a dictionary given a dot-separated field path.
    For example, get_nested_value(record, "int.hello") returns record["int"]["hello"] if it exists.
    """
    parts = field_path.split(".")
    current = record
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def convert_to_tinydb_format(data: List[Dict[str, Any]], original_filename: str) -> Optional[str]:
    """
    Convert a list of records into TinyDB compatible JSON format.
    For example:
      [{"int": 1, "char": "a"}, {"int": 1, "char": "b"}]
    becomes:
      {"_default": {"1": {"int": 1, "char": "a"}, "2": {"int": 1, "char": "b"}}}
    The converted file is saved as "originalfilename.db.json" in the same directory.
    Returns the new filename if successful.
    """
    new_data = {"_default": {}}
    for i, record in enumerate(data, start=1):
        new_data["_default"][str(i)] = record

    base, _ = os.path.splitext(original_filename)
    new_filename = base + ".db.json"
    try:
        with open(new_filename, "w", encoding="utf-8", errors="replace") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
        return new_filename
    except Exception as e:
        print(f"Error saving converted file: {e}")
        return None


class Console(BufferedCmd):
    CMD_CATEGORY = CMD_CATEGORY

    def __init__(self, *args, **kwargs) -> None:
        # Load environment variables from a .env file
        load_dotenv()
        super().__init__(*args, **kwargs)
        self.prompt = "JSON CLI> "
        self.intro = cmd2.style("Welcome to json-manager CLI", fg=cmd2.Fg.GREEN, bold=True)

        # Example settable value (for configuration)
        self.settable_value: int = 12
        self.add_settable(cmd2.Settable("settable_value", str, "Settable value description", self))

        # Database and file storage variables
        self.db: Optional[TinyDB] = None
        self.file_path: Optional[str] = None

    def ensure_db(self) -> bool:
        """
        Ensure that the database is loaded. If not, try to load it from the stored file_path.
        Returns True if the database is available, otherwise False.
        """
        if self.db is None:
            if self.file_path and os.path.exists(self.file_path):
                try:
                    self.db = TinyDB(self.file_path, storage=UTF8ReplaceJSONStorage)
                    # https://tinydb.readthedocs.io/en/latest/usage.html
                    # self.db = TinyDB(self.file_path, storage=CachingMiddleware(MemoryStorage))
                    # db = TinyDB(self.file_path, sort_keys=True, indent=4, separators=(',', ': '))
                    # db = TinyDB(self.file_path, ensure_ascii=False, indent=4, separators=(',', ': '))
                    self.poutput("Database loaded from file.")
                except Exception as e:
                    self.perror(f"Error loading database from file: {e}")
                    return False
            else:
                self.perror("No database loaded. Please load a JSON file first.")
                return False
        return True

    def load_json(self, source: str) -> None:
        """
        Load JSON data from a local file or a URL and initialize TinyDB.
        If the data is a list, it is converted into TinyDB format and saved as "filename.db.json"
        in the same directory as the source.
        If the data is a dict, it is verified to be TinyDB-compatible (i.e. contains "_default"
        whose value is a dict). Otherwise, a warning is printed and the original file_path is retained.
        
        :param source: Path to a local JSON file or a URL pointing to JSON data.
        """
        data = None
        # Save previous file path in case of error
        previous_file_path = self.file_path

        if source.startswith("http://") or source.startswith("https://"):
            try:
                response = requests.get(source)
                response.raise_for_status()
                data = response.json()
                # Save downloaded JSON temporarily as "downloaded.json"
                # self.file_path = "downloaded.json"
                # with open(self.file_path, "w", encoding="utf-8", errors="replace") as f:
                #     json.dump(data, f, ensure_ascii=False, indent=4)
                self.file_path = download_json(url=source)
            except Exception as e:
                self.perror(f"Error downloading JSON: {e}")
                self.file_path = previous_file_path
                return
        else:
            self.file_path = source
            try:
                with open(source, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
            except Exception as e:
                self.perror(f"Error reading JSON file: {e}")
                self.file_path = previous_file_path
                return

        # Check the data format:
        if isinstance(data, list):
            new_filename = convert_to_tinydb_format(data, self.file_path)
            if new_filename:
                self.poutput(f"Converted list to TinyDB format and saved as {new_filename}")
                self.file_path = new_filename
            else:
                self.perror("Conversion to TinyDB format failed.")
                self.file_path = previous_file_path
                return
        elif isinstance(data, dict):
            if "_default" not in data or not isinstance(data["_default"], dict):
                self.perror("JSON file is not in TinyDB compatible format. It must have a '_default' key with a dict value.")
                self.file_path = previous_file_path
                return
        else:
            self.perror("Unsupported JSON format.")
            self.file_path = previous_file_path
            return

        # Load the TinyDB database using our custom storage
        try:
            self.db = TinyDB(self.file_path, storage=UTF8ReplaceJSONStorage)
            self.poutput("JSON data loaded successfully into TinyDB.")
        except Exception as e:
            self.perror(f"Error loading JSON file into TinyDB: {e}")
            self.file_path = previous_file_path

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

    def insert_record(self, record_str: str) -> None:
        """
        Insert a new record into the database.
        
        :param record_str: A string representation of a JSON record.
        """
        if not self.ensure_db():
            return

        try:
            record: Dict[str, Any] = json.loads(record_str)
            self.db.insert(record)
            self.poutput("Record inserted successfully.")
        except json.JSONDecodeError:
            self.perror("Invalid JSON record provided.")
        except Exception as e:
            self.perror(f"Error inserting record: {e}")

    insert_parser = cmd2.Cmd2ArgumentParser()
    insert_parser.add_argument("record", help="JSON string representing the record to insert")
    
    @cmd2.with_argparser(insert_parser)
    @cmd2.with_category(CMD_CATEGORY)
    def do_insert(self, args: Any) -> None:
        """
        Insert a new record into the JSON database.
        
        Usage: insert <json_record>
        Example: insert '{"name": "Alice", "age": 30}'
        """
        self.insert_record(args.record)

    # ---------------------------
    # SEARCH COMMAND (Exact, Contains, Regex, or Case-Insensitive Contains Match)
    # ---------------------------
    search_parser = cmd2.Cmd2ArgumentParser()
    search_parser.add_argument("value", help="Value to search for. For objects, provide a JSON string.")
    search_parser.add_argument(
        "--field",
        action="append",
        required=True,
        help="Field(s) to search in. Use dot notation for nested fields (e.g. int.hello)."
    )
    search_parser.add_argument(
        "--contains",
        action="store_true",
        help="If provided, check if the field value contains the search query as a substring."
    )
    search_parser.add_argument(
        "--icontains",
        action="store_true",
        help="If provided, check if the field value contains the search query as a substring (case-insensitive)."
    )
    search_parser.add_argument(
        "--regex",
        action="store_true",
        help="If provided, treat the search value as a regular expression and match using re.search()."
    )
    
    @cmd2.with_argparser(search_parser)
    @cmd2.with_category(CMD_CATEGORY)
    def do_search(self, args: Any) -> None:
        """
        Search for records where any of the specified fields match the given value.
        By default, the search requires an exact match (or deep equality if the value is JSON).
        If the --contains flag is provided, the search checks if the field value (converted to string)
        contains the search query as a substring.
        If the --icontains flag is provided, the search performs a case-insensitive substring match.
        If the --regex flag is provided, the search treats the search value as a regular expression.
        Prints out the entire matching object.
        
        Usage: search <value> --field <field1> [--field <field2> ...] [--contains] [--icontains] [--regex]
        """
        if not self.ensure_db():
            return

        # If not using contains, icontains, or regex, try to parse the search value as JSON for deep equality.
        use_json = False
        if not (args.contains or args.icontains or args.regex):
            try:
                search_value = json.loads(args.value)
                use_json = True
            except Exception:
                search_value = args.value
        else:
            search_value = args.value

        results_found = False
        for record in self.db.all():
            for field in args.field:
                field_val = get_nested_value(record, field)
                if field_val is not None:
                    str_field_val = str(field_val)
                    if args.regex:
                        if re.search(search_value, str_field_val):
                            self.poutput(f"Match found in field '{field}' (regex match):")
                            self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
                            results_found = True
                            break
                    elif args.icontains:
                        if search_value.lower() in str_field_val.lower():
                            self.poutput(f"Match found in field '{field}' (case-insensitive contains match):")
                            self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
                            results_found = True
                            break
                    elif args.contains:
                        if search_value in str_field_val:
                            self.poutput(f"Match found in field '{field}' (contains match):")
                            self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
                            results_found = True
                            break
                    else:
                        if use_json:
                            if field_val == search_value:
                                self.poutput(f"Match found in field '{field}' (exact JSON match):")
                                self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
                                results_found = True
                                break
                        else:
                            if str_field_val == args.value:
                                self.poutput(f"Match found in field '{field}' (exact string match):")
                                self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
                                results_found = True
                                break
            # Continue to next record after processing fields.
        if not results_found:
            self.poutput("No matching records found.")

    # ---------------------------
    # FUZZY SEARCH COMMAND
    # ---------------------------
    fuzzy_parser = cmd2.Cmd2ArgumentParser()
    fuzzy_parser.add_argument("search_term", help="Term to fuzzy search for")
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
    @cmd2.with_category(CMD_CATEGORY)
    def do_fuzzy_search(self, args: Any) -> None:
        """
        Perform a fuzzy search on records using the specified fields.
        For each record, each specified field is checked using fuzzy matching.
        Matching records are sorted in descending order by score and then printed.
        
        Usage: fuzzy_search <search_term> --field <field1> [--field <field2> ...] [--threshold <score>]
        """
        if not self.ensure_db():
            return

        threshold = args.threshold
        matches: List[Tuple[Dict[str, Any], str, Any, int]] = []  # (record, field, field_val, score)

        for record in self.db.all():
            for field in args.field:
                field_val = get_nested_value(record, field)
                if field_val is not None:
                    score = fuzz.ratio(args.search_term, str(field_val))
                    if score >= threshold:
                        matches.append((record, field, field_val, score))
                        # Continue checking other fields for potential better scores

        if matches:
            # Sort matches by score descending
            matches.sort(key=lambda x: x[3], reverse=True)
            for record, field, field_val, score in matches:
                self.poutput(f"Record match (field '{field}' with value '{field_val}', score: {score}):")
                self.poutput(json.dumps(record, indent=4, ensure_ascii=False))
        else:
            self.poutput("No fuzzy matching records found.")

    @cmd2.with_category(CMD_CATEGORY)
    def do_open_json(self, args: Any) -> None:
        """
        Open the currently loaded JSON file using the default editor specified in the EDITOR environment variable.
        
        Usage: open_json
        """
        if self.file_path is None or not os.path.exists(self.file_path):
            self.perror("No JSON file loaded. Please load a JSON file first.")
            return

        editor = os.getenv("EDITOR")
        if not editor:
            self.perror("Environment variable EDITOR is not set. Please set it to your preferred text editor.")
            return

        try:
            subprocess.run([editor, self.file_path])
        except Exception as e:
            self.perror(f"Error opening JSON file: {e}")

    @cmd2.with_category(CMD_CATEGORY)
    def do_status(self, args: Any) -> None:
        """
        Display the current system status including loaded file and database information.
        
        Usage: status
        """
        status_info = []
        if self.file_path:
            status_info.append(f"Loaded file: {self.file_path}")
        else:
            status_info.append("No file loaded.")
        
        if self.db is None:
            status_info.append("Database not loaded.")
        else:
            try:
                record_count = len(self.db.all())
                status_info.append(f"Database loaded with {record_count} record(s).")
            except Exception as e:
                status_info.append(f"Error retrieving record count: {e}")
                if "list object has no attribute 'items'" in str(e):
                    status_info.append("It appears the JSON file may not be in TinyDB format. "
                                       "Ensure it is a JSON object with a table key (e.g., '_default').")
        
        for line in status_info:
            self.poutput(line)


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
    sys.exit(c.cmdloop())


if __name__ == "__main__":
    main()
