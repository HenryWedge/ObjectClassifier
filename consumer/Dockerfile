FROM python:3.10-bookworm

WORKDIR /app

COPY sut/ObjectClassifier/consumer/requirements.txt requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY sut/ObjectClassifier/consumer/object_classifier object_classifier

CMD ["python3", "object_classifier/consumer.py"]
