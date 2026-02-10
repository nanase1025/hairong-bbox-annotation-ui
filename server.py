import argparse
import json
import os

from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

DATA_DIR = ""
OUTPUT_FILE = ""
OUTPUT_DATA = {}  # {episode_id: annotation_text}
SAMPLES = []  # list of (image_filename, json_filename) pairs

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def scan_data_dir(data_dir):
    """Scan data directory for image files (with optional JSON pairs)."""
    samples = []
    seen = set()
    for fname in sorted(os.listdir(data_dir)):
        name, ext = os.path.splitext(fname)
        if ext.lower() in IMAGE_EXTENSIONS and name not in seen:
            json_file = name + ".json"
            json_path = os.path.join(data_dir, json_file)
            if os.path.isfile(json_path):
                samples.append((fname, json_file))
            else:
                samples.append((fname, None))
            seen.add(name)
    return samples


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/samples")
def api_samples():
    return jsonify({"total": len(SAMPLES)})


@app.route("/api/sample/<int:idx>")
def api_sample(idx):
    if idx < 0 or idx >= len(SAMPLES):
        return jsonify({"error": "Index out of range"}), 404
    image_file, json_file = SAMPLES[idx]
    data = {}
    if json_file:
        json_path = os.path.join(DATA_DIR, json_file)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    episode_id = os.path.splitext(image_file)[0]
    return jsonify(
        {
            "index": idx,
            "image_url": f"/images/{image_file}",
            "bbox": data.get("bbox", None),
            "label": data.get("label", ""),
            "text": OUTPUT_DATA.get(episode_id, ""),
        }
    )


@app.route("/api/sample/<int:idx>/save", methods=["POST"])
def api_save(idx):
    if idx < 0 or idx >= len(SAMPLES):
        return jsonify({"error": "Index out of range"}), 404
    image_file, _ = SAMPLES[idx]
    episode_id = os.path.splitext(image_file)[0]
    body = request.get_json()
    OUTPUT_DATA[episode_id] = body.get("text", "")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(OUTPUT_DATA, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(DATA_DIR, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bbox Annotation UI Server")
    parser.add_argument(
        "--data-dir", required=True, help="Path to data directory with image+JSON pairs"
    )
    parser.add_argument(
        "--output-file", required=True, help="Path to output JSON file for annotations"
    )
    parser.add_argument("--port", type=int, default=5000, help="Port to run server on")
    args = parser.parse_args()

    DATA_DIR = os.path.abspath(args.data_dir)
    if not os.path.isdir(DATA_DIR):
        print(f"Error: {DATA_DIR} is not a valid directory")
        exit(1)

    OUTPUT_FILE = os.path.abspath(args.output_file)
    if os.path.isfile(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            OUTPUT_DATA = json.load(f)
        print(f"Loaded {len(OUTPUT_DATA)} existing annotations from {OUTPUT_FILE}")
    else:
        OUTPUT_DATA = {}
        print(f"Output file: {OUTPUT_FILE} (new)")

    SAMPLES = scan_data_dir(DATA_DIR)
    print(f"Found {len(SAMPLES)} samples in {DATA_DIR}")

    app.run(host="0.0.0.0", port=args.port, debug=True)
