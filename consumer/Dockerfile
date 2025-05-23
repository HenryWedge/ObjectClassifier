FROM python:3.10-bookworm

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python3 -m pip install -r requirements.txt

COPY object_classifier object_classifier
COPY setup.py setup.py
COPY dog.jpg dog.jpg
RUN ["python3", "setup.py"]

CMD python3 object_classifier/consumer.py