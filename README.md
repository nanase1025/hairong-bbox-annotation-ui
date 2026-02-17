# Bbox Annotation UI

## Quick Start

1) Download the dataset zip:
https://drive.google.com/file/d/1yNFahFV5pliA88QwCIxdYMp_K5yFNitX/view?usp=drive_link

2) Unzip:
```bash
unzip human200.zip -d /path/to/data
```

3) Run:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python server_bbox.py \
  --data-dir /path/to/data \
  --intention-file /path/to/data/intentions.json \
  --group-file /path/to/data/groups.json \
  --output-file /path/to/hairong-bbox-annotation-ui/bbox_output.json
```

4) Open:
http://localhost:5001
You will see the annotation guidelines and examples on the page.

5) Select your assigned Group and annotate only that group.
Rename the output file as `yourname_group1.json` or `yourname_group2.json` and submit to:
https://drive.google.com/drive/folders/1yF46jRkayuar_L1O79kaEFqWv0z62Iq8?usp=drive_link
