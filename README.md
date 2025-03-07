# JSON Manager

JSON Manager is a versatile command-line tool for managing JSON files, featuring two specialized console interfaces:

- **DB Console**: For JSON files compatible with TinyDB, enabling database-like operations.
- **JSON Console**: For general JSON files, offering basic inspection and editing capabilities.

JSON Manager automatically determines the appropriate interface based on the loaded data structure, including support for downloading JSON directly from URLs.

---

## Features

- **Dual-Console Interface**:
  - Automatically selects between DB and JSON console based on JSON structure.
- DB Console supports database operations (insert, search, fuzzy search) via TinyDB.
  - Custom UTF-8 Storage handling for improved compatibility.
  - Automatic JSON format conversion for TinyDB compatibility.
- **Remote JSON Loading**: Directly load JSON data from URLs into a local environment.
- **Buffered Command Interface**: Enhanced interaction built on `cmd2`, supporting command history, colorized output, and configurable prompts.
- **Persistent Data Management**: Automatic data synchronization to disk after command execution.

## Features

- Load JSON from local files or URLs.
- Insert new records into JSON lists.
- Comprehensive search functionalities:
  - Exact match
  - Substring match (case-sensitive and case-insensitive)
  - Regex matching
  - Fuzzy matching using `thefuzz` library
- Open JSON files in the system’s default editor via `EDITOR` environment variable.
- Detailed status command to inspect current loaded data.

---

## Prerequisites

- Python 3.6+
- Dependencies:
  - `cmd2`
  - `tinydb`
  - `requests`
  - `thefuzz`
  - `python-dotenv`

Install dependencies with:
```bash
pip install cmd2 tinydb requests thefuzz python-dotenv
```

## Project Structure

```
src/
└── json_manager
    ├── __init__.py
    ├── db_console.py         # TinyDB-based operations
    ├── json_console.py       # General JSON handling
    ├── buffered_cmd2.py      # Enhanced cmd2 console interface
    └── main.py               # Entry point, dynamically selects the console
```

## Usage

### Launching the JSON Manager CLI

From the project root directory:
```bash
python src/json_manager/main.py [--json <path_or_url>]
```

### Common Commands

- **Load JSON**
```bash
load <path_or_url>
```

- **Insert Record** (only when data is a list):
```bash
insert '{"name": "Alice", "age": 30}'
```

- **Search Records**
```bash
search <value> --field <field1> [--contains|--icontains|--regex]
```

- **Fuzzy Search**
```bash
fuzzy_search <search_term> --field <field> [--threshold <score>]
```

- **Open JSON in Editor**
```bash
open_json
```

- **Check Status**
```bash
status
```

## Environment Configuration

Ensure your preferred text editor is set in your environment:
```bash
export EDITOR=nano
```

## Custom Storage Handling

The tool uses a custom TinyDB storage class (`UTF8ReplaceJSONStorage`) to handle UTF-8 decoding errors gracefully, replacing problematic characters to avoid crashes.

## Dependencies

- `cmd2`
- `tinydb`
- `requests`
- `thefuzz`
- `python-dotenv`

## Notes

- The tool automatically determines whether to use DB Console or JSON Console based on the structure of the JSON file.
- All changes to JSON data are immediately synchronized to disk.

---

**Happy JSON managing!**

