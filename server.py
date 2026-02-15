import argparse
import json
import os

from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

DATA_DIR = ""
OUTPUT_FILE = ""
OUTPUT_DATA = {}  # {episode_id: annotation_text}
OUTPUT_GROUP = ""  # "1" or "2"
SAMPLES = []  # list of image filenames
CATEGORY_MAP = {}  # {image_filename or episode_id: category}
EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), "example")
EXAMPLE_DATA = []  # list of {image_url, category, intention}
GROUP_SAMPLES = {}  # {"1": [samples], "2": [samples]}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def scan_data_dir(data_dir):
    """Scan data directory recursively for image files."""
    samples = []
    seen = set()
    for root, _, files in os.walk(data_dir):
        for fname in sorted(files):
            name, ext = os.path.splitext(fname)
            if ext.lower() not in IMAGE_EXTENSIONS or name in seen:
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, data_dir)
            samples.append(rel_path)
            seen.add(name)
    return sorted(samples)


def load_category_map(path):
    if not path or not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    mapped = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        fname = os.path.basename(key)
        stem = os.path.splitext(fname)[0]
        mapped[key] = value
        mapped[fname] = value
        mapped[stem] = value
    return mapped


def load_examples():
    example_path = os.path.join(EXAMPLE_DIR, "example.json")
    if not os.path.isfile(example_path):
        return []
    with open(example_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    examples = []
    for rel_path, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        examples.append(
            {
                "image_url": f"/examples/{rel_path}",
                "category": payload.get("category", ""),
                "intention": payload.get("intention", ""),
            }
        )
    return examples


def _episode_id_from_path(image_path):
    return os.path.splitext(os.path.basename(image_path))[0]


def count_annotated(samples):
    sample_ids = {_episode_id_from_path(p) for p in samples}
    return sum(1 for key in OUTPUT_DATA.keys() if key in sample_ids)


def load_group_map(path):
    if not path or not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    mapped = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        group = str(value).strip()
        if group not in {"1", "2"}:
            continue
        fname = os.path.basename(key)
        stem = os.path.splitext(fname)[0]
        mapped[key] = group
        mapped[fname] = group
        mapped[stem] = group
    return mapped


def build_groups_from_map(samples, group_map):
    groups = {"1": [], "2": []}
    for image_path in samples:
        key = image_path
        base = os.path.basename(image_path)
        stem = os.path.splitext(base)[0]
        group = group_map.get(key) or group_map.get(base) or group_map.get(stem)
        if group in groups:
            groups[group].append(image_path)
    return groups


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/samples")
def api_samples():
    group = request.args.get("group") or "1"
    samples = GROUP_SAMPLES.get(group, [])
    return jsonify({"total": len(samples), "annotated": count_annotated(samples)})


@app.route("/api/examples")
def api_examples():
    return jsonify({"examples": EXAMPLE_DATA})


@app.route("/api/groups")
def api_groups():
    return jsonify(
        {
            "groups": {
                gid: {"total": len(samples), "annotated": count_annotated(samples)}
                for gid, samples in GROUP_SAMPLES.items()
                if samples
            }
        }
    )


@app.route("/api/sample/<int:idx>")
def api_sample(idx):
    group = request.args.get("group") or "1"
    samples = GROUP_SAMPLES.get(group, [])
    if idx < 0 or idx >= len(samples):
        return jsonify({"error": "Index out of range"}), 404
    image_file = samples[idx]
    episode_id = _episode_id_from_path(image_file)
    base_name = os.path.basename(image_file)
    base_stem = os.path.splitext(base_name)[0]
    category = (
        CATEGORY_MAP.get(image_file)
        or CATEGORY_MAP.get(episode_id)
        or CATEGORY_MAP.get(base_name)
        or CATEGORY_MAP.get(base_stem)
        or ""
    )
    return jsonify(
        {
            "index": idx,
            "image_url": f"/images/{image_file}",
            "category": category,
            "text": OUTPUT_DATA.get(episode_id, ""),
        }
    )


@app.route("/api/sample/<int:idx>/save", methods=["POST"])
def api_save(idx):
    group = request.args.get("group") or "1"
    samples = GROUP_SAMPLES.get(group, [])
    if idx < 0 or idx >= len(samples):
        return jsonify({"error": "Index out of range"}), 404
    image_file = samples[idx]
    episode_id = _episode_id_from_path(image_file)
    global OUTPUT_GROUP
    body = request.get_json()
    if OUTPUT_GROUP and OUTPUT_GROUP != group:
        return (
            jsonify({"error": f"Output file locked to group {OUTPUT_GROUP}."}),
            400,
        )
    if not OUTPUT_GROUP:
        OUTPUT_GROUP = group
    text = body.get("text", "")
    if text is None:
        text = ""
    text = text.strip()
    if text:
        OUTPUT_DATA[episode_id] = text
    else:
        OUTPUT_DATA.pop(episode_id, None)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        payload = {"__group__": OUTPUT_GROUP, **OUTPUT_DATA}
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(DATA_DIR, filename)


@app.route("/examples/<path:filename>")
def serve_example(filename):
    return send_from_directory(EXAMPLE_DIR, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bbox Annotation UI Server")
    parser.add_argument(
        "--data-dir", required=True, help="Path to data directory with images"
    )
    parser.add_argument(
        "--output-file", required=True, help="Path to output JSON file for annotations"
    )
    parser.add_argument(
        "--category-file",
        default="",
        help="Path to categories JSON (optional, defaults to data_dir/categories.json if present)",
    )
    parser.add_argument(
        "--group-file",
        default="",
        help="Path to groups JSON (optional, defaults to data_dir/groups.json if present)",
    )
    parser.add_argument("--port", type=int, default=5000, help="Port to run server on")
    args = parser.parse_args()

    DATA_DIR = os.path.abspath(args.data_dir)
    if not os.path.isdir(DATA_DIR):
        print(f"Error: {DATA_DIR} is not a valid directory")
        exit(1)

    OUTPUT_FILE = os.path.abspath(args.output_file)
    if os.path.isfile(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                contents = f.read().strip()
            OUTPUT_DATA = json.loads(contents) if contents else {}
            if isinstance(OUTPUT_DATA, dict) and "__group__" in OUTPUT_DATA:
                OUTPUT_GROUP = str(OUTPUT_DATA.pop("__group__"))
        except json.JSONDecodeError:
            OUTPUT_DATA = {}
            print(f"Warning: {OUTPUT_FILE} is not valid JSON, starting fresh.")
        print(f"Loaded {len(OUTPUT_DATA)} existing annotations from {OUTPUT_FILE}")
    else:
        OUTPUT_DATA = {}
        print(f"Output file: {OUTPUT_FILE} (new)")

    category_file = (
        os.path.abspath(args.category_file)
        if args.category_file
        else os.path.join(DATA_DIR, "categories.json")
    )
    CATEGORY_MAP = load_category_map(category_file)

    EXAMPLE_DATA = load_examples()

    SAMPLES = scan_data_dir(DATA_DIR)
    group_file = (
        os.path.abspath(args.group_file)
        if args.group_file
        else os.path.join(DATA_DIR, "groups.json")
    )
    group_map = load_group_map(group_file)
    GROUP_SAMPLES = build_groups_from_map(SAMPLES, group_map)
    print(f"Found {len(SAMPLES)} samples in {DATA_DIR}")

    app.run(host="0.0.0.0", port=args.port, debug=True)
