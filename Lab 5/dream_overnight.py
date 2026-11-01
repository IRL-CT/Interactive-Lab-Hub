
from ultralytics import YOLO
from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import time

# Configuration
BASE_DIR = Path(__file__).resolve().parent

PHOTO_DIR = BASE_DIR / "dream_photos"
LOG_FILE = BASE_DIR / "dream_log.jsonl"
MODEL_PATH = BASE_DIR / "yolo26n_ncnn_model"

CONFIDENCE = 0.25
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def interpret(result, model):
    """Convert YOLO detections into meaningful observations."""

    objects = []
    names = []

    for box in result.boxes:
        label = model.names[int(box.cls[0])]
        confidence = float(box.conf[0])

        objects.append({
            "name": label,
            "confidence": round(confidence, 2)
        })

        names.append(label)

    # Count repeated objects
    counts = Counter(names)

    if counts:
        description = ", ".join(
            f"{count} {name}{'s' if count > 1 else ''}"
            for name, count in counts.items()
        )
    else:
        description = "No recognizable objects"

    return objects, description


def process_photos():
    """Process uploaded photos and save YOLO observations."""

    if not PHOTO_DIR.exists():
        raise FileNotFoundError(
            f"Photo directory not found: {PHOTO_DIR}"
        )

    images = sorted(
        p for p in PHOTO_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower() in VALID_EXTENSIONS
    )

    if not images:
        raise SystemExit("No photos found!")

    print(f"Found {len(images)} photos.", flush=True)
    print("Loading YOLO model...", flush=True)

    model = YOLO(str(MODEL_PATH), task="detect")

    start_time = time.time()
    processed = 0
    failed = 0

    with LOG_FILE.open("w", encoding="utf-8") as log:
        for index, image in enumerate(images, start=1):
            try:
                results = model.predict(
                    source=str(image),
                    conf=CONFIDENCE,
                    verbose=False
                )

                objects, description = interpret(
                    results[0], model
                )

                reading = {
                    "timestamp": datetime.now().isoformat(),
                    "image": image.name,
                    "objects": objects,
                    "description": description
                }

                log.write(
                    json.dumps(reading, ensure_ascii=False) + "\n"
                )
                log.flush()

                processed += 1

                print(
                    f"[{index}/{len(images)}] "
                    f"{image.name}: {description}",
                    flush=True
                )

            except Exception as e:
                failed += 1
                print(
                    f"Error processing {image.name}: {e}",
                    flush=True
                )

    elapsed = time.time() - start_time

    print("\n===== PROCESSING COMPLETE =====", flush=True)
    print(f"Photos processed: {processed}", flush=True)
    print(f"Photos failed: {failed}", flush=True)
    print(f"Time elapsed: {elapsed:.1f} seconds", flush=True)
    print(f"Log saved to: {LOG_FILE}", flush=True)

    if processed == 0:
        raise RuntimeError("No photos were processed successfully.")


if __name__ == "__main__":
    process_photos()
