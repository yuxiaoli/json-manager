# JSON Manager

JSON Manager is a command-line interface (CLI) tool for managing JSON files in multiple formats. It provides two distinct consoles for working with JSON data:

- **Database Console:** Launched when the JSON file is TinyDB‑compatible (i.e. contains a `_default` key with a dict value) or when the JSON is a list. This console leverages TinyDB for database-like operations.
- **JSON Console:** Launched for JSON files that do not match the TinyDB format, offering commands for inspecting and modifying standard JSON objects.

The tool also supports downloading JSON data from a URL into a temporary directory and then processing it accordingly.

---

## Features

- **Flexible JSON Loading:**  
  Load JSON files from local paths or remote URLs.  
- **Automatic Format Detection:**  
  The tool inspects the JSON structure and automatically selects the appropriate console (database or JSON) based on the format.
- **Rich Command-Line Interface:**  
  Built on top of [cmd2](https://cmd2.readthedocs.io/), it offers a variety of commands such as:
  - `load` to load a JSON file or URL.
  - `insert` to add records.
  - `search` and `fuzzy_search` for finding records.
  - `open_json` to open the file with your default editor.
  - `status` to view the current state of the loaded data.
- **TinyDB Integration:**  
  For JSON files in TinyDB format, enjoy database operations with TinyDB.
- **Customizable Environment:**  
  Leverage environment variables (e.g., `EDITOR`) for a personalized setup.

---

## Prerequisites

- **Python:** 3.6+
- **Required Python Libraries:**
  - `cmd2`
  - `tinydb`
  - `requests`
  - `thefuzz`
  - `python-dotenv`

Install the required libraries with:

```bash
pip install cmd2 tinydb requests thefuzz python-dotenv
```

---

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone <repository_url>
cd json_manager
```

---

## Project Structure

```
json_manager/
├── __init__.py
├── db_console.py        # CLI for TinyDB-compatible or list JSON files.
├── buffered_cmd2.py     # Custom cmd2 subclass for buffered command output.
├── json_console.py      # CLI for general JSON files.
└── main.py              # Entry point: selects and launches the appropriate console.
```

---

## Usage

Run the project using the main entry script. The script accepts a required positional argument for the JSON file or URL, and an optional `--temp` argument for specifying a temporary directory when downloading files:

```bash
python main.py <path_or_url_to_json> [--temp <temp_directory>]
```

### Examples

- **Load a local JSON file:**

  ```bash
  python main.py data/sample.json
  ```

- **Download and load a JSON file from a URL (saved to the default `temp/` directory):**

  ```bash
  python main.py https://example.com/data.json
  ```

- **Specify a custom temporary directory:**

  ```bash
  python main.py https://example.com/data.json --temp /path/to/temp/
  ```

Based on the JSON structure, the tool will automatically launch either the **database console** or the **JSON console**. Within these consoles, you can use commands like:

- `load` — Load a new JSON file or URL.
- `insert` — Insert new records into the data.
- `search` and `fuzzy_search` — Find records using exact or fuzzy matching.
- `open_json` — Open the current JSON file in your preferred editor.
- `status` — Display details about the loaded file and data.

---

## Contributing

Contributions are welcome! If you have suggestions, improvements, or bug fixes, please open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [cmd2](https://cmd2.readthedocs.io/)
- [TinyDB](https://tinydb.readthedocs.io/)
- [thefuzz](https://github.com/seatgeek/thefuzz)
- [Requests](https://docs.python-requests.org/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

Enjoy using JSON Manager!