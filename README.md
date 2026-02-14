# Bbox Annotation UI

A local web tool for adding text annotations to image + bbox + label datasets.

## Input Data Structure

```
data_dir/
  <episode_id>.png
  <episode_id>.json
  ...
```

- Place image files (`.png` / `.jpg` / `.jpeg` / `.webp`) in the directory.
- If a JSON file with the same name exists, bbox and label info will be loaded. JSON files are optional.

### JSON File Format

```json
{
  "bbox": [x1, y1, x2, y2], # optional
  "label": "cat"
}
```

| Field   | Type                               | Required | Description                                                                                               |
| ------- | ---------------------------------- | -------- | --------------------------------------------------------------------------------------------------------- |
| `bbox`  | `[number, number, number, number]` | No       | Top-left (x1, y1) and bottom-right (x2, y2) pixel coordinates. Displayed as a red rectangle on the image. |
| `label` | `string`                           | No       | Label string. Displayed below the image.                                                                  |

## Output File

Annotations are saved to the JSON file specified by `--output-file`.

```json
{
  "<episode_id>": "annotation text",
  "<episode_id>": "annotation text"
}
```

- Keys are image filenames without extensions (e.g., `image1.png` -> `"image1"`).
- If the output file already exists, it will be loaded so you can resume from where you left off.

## Usage

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python server.py --data-dir /path/to/data --output-file /path/to/output.json
```

Open http://localhost:5000 in your browser.

### Options

| Argument        | Required | Default | Description                             |
| --------------- | -------- | ------- | --------------------------------------- |
| `--data-dir`    | Yes      | -       | Directory containing image + JSON pairs |
| `--output-file` | Yes      | -       | Output JSON file for annotation results |
| `--port`        | No       | `5000`  | Server port number                      |
