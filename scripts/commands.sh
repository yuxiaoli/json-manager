# Command reference only. Copy individual examples; never execute/source this file.
# Shell examples: Bash, project root. Console examples are comments: copy their text
# WITHOUT the leading "# " into the running JSON CLI, not into a shell.
# Replace YOUR_* paths/URLs with disposable data you control; no private examples are included.
# Prerequisites: Poetry, Python >=3.10,<4.0 (manifest supersedes README's Python 3.6).
# poetry.lock records Python ^3.11 despite the manifest's ^3.10; use Python 3.11+.
# Lock freshness has not been runtime-verified; if Poetry rejects it, reconcile separately.
# Install the package and dependencies; this registers jsoncli.
poetry install

# Show the TOP-LEVEL parser: input is REQUIRED and positional, not --json.
poetry run jsoncli --help

# Open a local JSON file; lists and TinyDB "_default" objects select the DB console.
# Other objects select the JSON console. Loading is NOT read-only:
# lists overwrite a sibling <stem>.db.json; JSON-console loading rewrites the original file.
# Work on copies and back up existing .db.json files first; there is no dry-run mode.
poetry run jsoncli "YOUR_INPUT/records.json"

# Alternative: download from a URL into a chosen temporary directory (created automatically).
# NETWORK/WRITE: uses the URL basename, adding .json if needed; same-name files are overwritten.
# Replace example.invalid with your authorized JSON endpoint; do not embed credentials in URLs.
poetry run jsoncli "https://example.invalid/YOUR_DATA/records.json" --temp "YOUR_OUTPUT/downloads"

# Alternative: launch either underlying console without loading data.
# These modules accept --json, unlike the top-level jsoncli command.
poetry run python -m json_manager.db_console

# Alternative: force general JSON handling (including lists without TinyDB conversion).
poetry run python -m json_manager.json_console --json "YOUR_INPUT/records.json"

# Alternative: explicitly load an existing TinyDB file; no list conversion needed.
poetry run python -m json_manager.db_console --json "YOUR_INPUT/records.db.json"

# Configure an installed editor before launching. EDITOR must be one executable, not flags.
# Replace nano with your installed editor; open_json launches it on the loaded file.
EDITOR=nano poetry run jsoncli "YOUR_INPUT/records.json"

# --- Commands INSIDE either running console ---
# Inspect command help, current file/data status, or clear the terminal.
# help
# help search
# status
# clear

# Load another local file. DB console requires a list or TinyDB object;
# JSON console accepts ordinary dicts/lists, rewrites the file, and remains the same console.
# load "YOUR_INPUT/records.json"

# Alternative: load a remote URL; console downloads use temp/ (not the top-level --temp override).
# Existing same-name downloads may be overwritten. Only use authorized public/sample data.
# load "https://example.invalid/YOUR_DATA/records.json"

# Insert a synthetic object; writes immediately. JSON console requires a list;
# DB console writes to the currently selected TinyDB file.
# insert '{"name":"Sample","age":30,"profile":{"city":"Example City"}}'

# Exact text or typed JSON values; repeated --field means ANY matching field, not all fields.
# Nested paths use dots. DB prints whole records; JSON console prints the matched field/value.
# search Sample --field name
# search 30 --field age
# search '{"city":"Example City"}' --field profile

# Case-sensitive substring search, or case-insensitive matching across multiple nested fields.
# Use only one search mode at a time: --regex takes precedence over --icontains over --contains.
# search Exam --field profile.city --contains
# search sample --field name --field profile.city --icontains

# KNOWN SOURCE BUG: --regex is registered but both handlers reference re without importing it.
# The following is syntax documentation ONLY, not a working command until source is fixed.
# search '^Sam' --field name --regex

# Fuzzy matching defaults to threshold 80; choose an explicit threshold across multiple fields.
# Results are sorted by score. JSON console also rewrites its loaded file after searches.
# fuzzy_search Sample --field name
# fuzzy_search Exampl --field name --field profile.city --threshold 70

# Open the loaded file in EDITOR (external edits can change data); reload deliberately afterward.
# open_json
# load "YOUR_INPUT/records.db.json"

# Leave the console using cmd2's quit command.
# quit

# No nonempty tests, lint configuration, deployment, or publishing workflow is defined.
# Runtime/console behavior is not validated by parsing this command reference.
