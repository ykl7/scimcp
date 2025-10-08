import json
import base64
import os
from pathlib import Path
from PIL import Image
from io import BytesIO

def extract_and_save_images_from_jsonl(jsonl_path, output_dir):
    """
    Reads a JSONL file and extracts base64-encoded images from 'artifacts'
    of type 'figure', saving them as JPEGs in the output directory.

    Args:
        jsonl_path (str or Path): Path to the input JSONL file.
        output_dir (str or Path): Directory to save extracted JPEG images.
    """
    os.makedirs(output_dir, exist_ok=True)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                entry = json.loads(line.strip())
                problem_id = entry.get("problem_id", f"figure_{idx:04d}")

                for i, artifact in enumerate(entry.get("artifacts", [])):
                    if artifact.get("type") == "figure":
                        base64_str = artifact["text"]
                        image_data = base64.b64decode(base64_str)
                        image = Image.open(BytesIO(image_data)).convert("RGB")

                        output_path = Path(output_dir) / f"{problem_id}_figure_{i}.jpeg"
                        image.save(output_path, format="JPEG")
                        print(f"Saved: {output_path}")

            except Exception as e:
                print(f"Failed to process line {idx}: {e}")

if __name__ == "__main__":
    # Example usage
    input_file = "gold_standard.jsonl"  # replace with your actual JSONL file
    output_folder = "decoded_figures"
    extract_and_save_images_from_jsonl(input_file, output_folder)