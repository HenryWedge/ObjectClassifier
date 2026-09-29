import base64
import json
import os
import random
import time
from pathlib import Path

from kafka import KafkaProducer


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def env_or_default(env_key, default_value):
    if env_key in os.environ:
        return os.environ[env_key]
    print(f"Warning! Env {env_key} not set using default value: {default_value}")
    return default_value


def parse_label_from_parent(image_path: Path) -> str:
    parent_name = image_path.parent.name
    if "-" in parent_name:
        return parent_name.split("-", 1)[1]
    return parent_name


def load_images(base_dir: Path):
    images = []
    for file_path in base_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(file_path)
    return sorted(images)


def build_payload(image_path: Path):
    with image_path.open("rb") as file_handle:
        encoded_image = base64.b64encode(file_handle.read()).decode("utf-8")

    return {
        "data": encoded_image,
        "timestamp": time.time(),
        "label": parse_label_from_parent(image_path),
    }


def main():
    bootstrap_servers = env_or_default("BOOTSTRAP_SERVER", "192.168.49.2:32092")
    topic = env_or_default("TOPIC", "dog-input")
    examples_dir = Path(
        env_or_default("EXAMPLES_DIR", "../../image-detection/producer/example")
    ).resolve()
    seed = int(env_or_default("SEED", "42"))
    send_interval_seconds = float(env_or_default("SEND_INTERVAL_SECONDS", "0.5"))

    if not examples_dir.exists() or not examples_dir.is_dir():
        raise FileNotFoundError(f"Examples directory not found: {examples_dir}")

    image_paths = load_images(examples_dir)
    if not image_paths:
        raise RuntimeError(f"No images found under {examples_dir}")

    rng = random.Random(seed)
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: str.encode(json.dumps(value)),
    )

    print(
        f"Starting producer with {len(image_paths)} images from {examples_dir}, "
        f"topic={topic}, seed={seed}"
    )

    while True:
        selected_image = rng.choice(image_paths)
        payload = build_payload(selected_image)

        producer.send(topic, payload)
        producer.flush()
        print(f"Sent {selected_image.name} label={payload['label']}")

        if send_interval_seconds > 0:
            time.sleep(send_interval_seconds)


if __name__ == "__main__":
    main()
