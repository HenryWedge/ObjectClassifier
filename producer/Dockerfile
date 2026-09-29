FROM python:3.10-bookworm

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY object_producer.py object_producer.py

CMD ["python3", "object_producer.py"]
