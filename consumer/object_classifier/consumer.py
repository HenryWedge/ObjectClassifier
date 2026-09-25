import base64
import json
import os
import time
from io import BytesIO
from threading import Thread

import numpy as np
from flask import Flask
from kafka import KafkaConsumer, KafkaProducer
from keras.api.preprocessing import image
from keras.src.applications.resnet_v2 import (
    ResNet50V2,
    ResNet101V2,
    ResNet152V2,
    decode_predictions,
    preprocess_input,
)
from PIL import Image
from prometheus_client import Counter, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from reporter import ClassificationReporter


def env_or_default(env_key, default_value):
    if env_key in os.environ:
        return os.environ[env_key]
    print(f"Warning! Env {env_key} not set using default value: {default_value}")
    return default_value


def get_model(depth):
    if depth == "50":
        return ResNet50V2(weights="imagenet")
    if depth == "101":
        return ResNet101V2(weights="imagenet")
    if depth == "152":
        return ResNet152V2(weights="imagenet")
    raise ValueError(f"Unsupported model depth: {depth}")


app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

messages_total = Counter(
    "object_classifier_messages_total",
    "Total number of processed messages",
)
matches_total = Counter(
    "object_classifier_matches_total",
    "Total number of exact label matches",
)
mismatches_total = Counter(
    "object_classifier_mismatches_total",
    "Total number of exact label mismatches",
)
processing_errors_total = Counter(
    "object_classifier_processing_errors_total",
    "Total number of processing errors",
)

inference_seconds = Histogram(
    "object_classifier_inference_seconds",
    "Inference processing time in seconds",
)
queue_delay_seconds = Histogram(
    "object_classifier_queue_delay_seconds",
    "Queueing delay in seconds",
)
end_to_end_latency_seconds = Histogram(
    "object_classifier_end_to_end_latency_seconds",
    "End-to-end latency in seconds",
)

bootstrap_servers = env_or_default("BOOTSTRAP_SERVER", "192.168.49.2:32092")
input_topic = env_or_default("TOPICS", "dog-input")
result_topic = env_or_default("REPORTER_TOPIC", "reporter")
model = get_model(env_or_default("MODEL_DEPTH", "152"))
max_poll_records = int(env_or_default("MAX_POLL_RECORDS", "50"))

consumer = KafkaConsumer(
    input_topic,
    bootstrap_servers=bootstrap_servers,
    group_id=env_or_default("GROUP_ID", "doggy5"),
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    max_poll_records=max_poll_records,
)
producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda value: str.encode(json.dumps(value)),
)


def process_messages():
    while True:
        for message in consumer:
            ingestion_time = time.time()
            try:
                image_data = message.value["data"].encode("utf-8")
                event_timestamp = float(message.value["timestamp"])
                event_label = str(message.value["label"])

                img = Image.open(BytesIO(base64.b64decode(image_data)))
                x = image.img_to_array(img.resize((224, 224), Image.Resampling.LANCZOS))
                x = np.expand_dims(x, axis=0)
                x = preprocess_input(x)

                preds = model.predict(x, verbose=0)
                processed_time = time.time()
                prediction = decode_predictions(preds, top=1)[0][0][1]
                matched = event_label == prediction

                report = ClassificationReporter(
                    event_time=event_timestamp,
                    ingestion_time=ingestion_time,
                    processed_time=processed_time,
                    actual_label=event_label,
                    prediction=prediction,
                    matched=matched,
                )

                producer.send(result_topic, report.__dict__)
                producer.flush()

                messages_total.inc()
                if matched:
                    matches_total.inc()
                else:
                    mismatches_total.inc()

                inference_seconds.observe(report.get_inference_time())
                queue_delay_seconds.observe(report.get_queueing_delay())
                end_to_end_latency_seconds.observe(report.get_processing_time())

                consumer.commit()
                print(f"Prediction={prediction} Actual={event_label} Match={matched}")
            except Exception as exc:
                processing_errors_total.inc()
                print(f"Message processing error: {exc}")


@app.route("/")
def index():
    return "Object Classifier"


if __name__ == "__main__":
    thread = Thread(target=process_messages)
    thread.start()
    app.run(host="0.0.0.0", port=5001)
