import json
import os
import time
from threading import Thread

import numpy as np
from kafka import KafkaConsumer, KafkaProducer
from keras.api.preprocessing import image
from keras.src.applications.resnet_v2 import ResNet50V2, preprocess_input, decode_predictions, ResNet101V2, ResNet152V2
import base64
from PIL import Image
from io import BytesIO
from flask import Flask
from prometheus_client import make_wsgi_app, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from averaging_window import AveragingWindow
from reporter import ClassificationReporter

def env_or_default(env_key, default_value):
    if env_key in os.environ:
        return os.environ[env_key]
    else:
        print(f"Warning! Env {env_key} not set using default value: {default_value}")
        return default_value

def get_model(depth):
    if depth == "50":
        return ResNet50V2(weights="imagenet")
    elif depth == "101":
        return ResNet101V2(weights="imagenet")
    elif depth == "152":
        return ResNet152V2(weights="imagenet")

app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

inference_time_gauge = Gauge(
'inference_time',
    'Inference Time',
)

latency_gauge = Gauge(
'latency',
    'Latency',
)

recall_gauge = Gauge(
'recall',
    'Recall',
)

precision_gauge = Gauge(
'precision',
    'Precision',
)

accuracy_gauge = Gauge(
'accuracy',
    'Accuracy',
)

f1_gauge = Gauge(
'f1score',
    'F1-Score',
)

bootstrap_servers = env_or_default("BOOTSTRAP_SERVER", "kube1-1:31815")
model = get_model(env_or_default("MODEL_DEPTH", "152"))
result_topic = env_or_default("REPORTER_TOPIC", "reporter")
inf_time_topic = env_or_default("INF_TIME_TOPIC", "inf_time")
metrics_window_size = env_or_default("METRICS_WINDOW_SIZE", "100")
max_poll_records = int(env_or_default("MAX_POLL_RECORDS", "50"))

consumer = KafkaConsumer(
    env_or_default("TOPICS", "dog-input"),
    bootstrap_servers=bootstrap_servers,
    group_id=env_or_default("GROUP_ID", "doggy5"),
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    max_poll_records=max_poll_records
)
producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda value: str.encode(json.dumps(value))
)

def update_gauge(gauge, timeseries, new_value):
    timeseries.append_value(new_value)
    gauge.set(timeseries.get_average())

def process_messages():
    averaging_window_latency = AveragingWindow(int(metrics_window_size))
    averaging_window_inference_time = AveragingWindow(int(metrics_window_size))

    averaging_window_accuracy = AveragingWindow(int(metrics_window_size))
    averaging_window_precision = AveragingWindow(int(metrics_window_size))
    averaging_window_recall = AveragingWindow(int(metrics_window_size))
    averaging_window_f1score = AveragingWindow(int(metrics_window_size))

    truth = []
    predictions = []
    while True:
        for message in consumer:
            image_data = message.value['data'].encode()
            event_timestamp = message.value['timestamp']
            event_label = message.value['label'].split("-")[1]

            ingestion_time = time.time()
            img = Image.open(BytesIO(base64.b64decode(image_data)))

            x = image.img_to_array(img.resize((224, 224), Image.Resampling.LANCZOS))
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)

            preds = model.predict(x)
            processed_time = time.time()
            prediction = decode_predictions(preds, top=3)[0][0][1]
            consumer.commit()

            report = ClassificationReporter(
                event_time=event_timestamp,
                ingestion_time=ingestion_time,
                processed_time=processed_time,
                actual_label=event_label,
                prediction=prediction
            )

            producer.send(result_topic, report.__dict__)
            update_gauge(gauge=inference_time_gauge, timeseries=averaging_window_inference_time, new_value=processed_time - ingestion_time)
            update_gauge(gauge=latency_gauge, timeseries=averaging_window_latency, new_value=processed_time - event_timestamp)

            accuracy = accuracy_score(truth, predictions)
            update_gauge(gauge=accuracy_gauge, timeseries=averaging_window_accuracy, new_value=accuracy)

            precision = precision_score(truth, predictions, average='weighted', zero_division=0.0)
            update_gauge(gauge=precision_gauge, timeseries=averaging_window_precision, new_value=precision)

            recall = recall_score(truth, predictions, average='weighted', zero_division=0.0)
            update_gauge(gauge=recall_gauge, timeseries=averaging_window_recall, new_value=recall)

            f1 = f1_score(truth, predictions, average='weighted', zero_division=0.0)
            update_gauge(gauge=f1_gauge, timeseries=averaging_window_f1score, new_value=f1)

            producer.flush()
            print(decode_predictions(preds, top=3)[0][0])
            print("Latency: ", processed_time - event_timestamp)

@app.route('/')
def index():
    return "Accuracy Monitor"

if __name__ == '__main__':
    thread = Thread(target=process_messages)
    thread.start()
    app.run(host='0.0.0.0', port=5001)