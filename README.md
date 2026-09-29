# ObjectClassifier Helm Deployment

This project is deployed via Helm chart in `helm/object-classifier`.

## Prerequisites

- Minikube running (`minikube status`)
- `kubectl`
- `helm`
- `docker`

## Build images

From this directory:

```bash
docker build -t ecoscape/object-classifier-consumer -f consumer/Dockerfile .
docker build -t ecoscape/object-classifier-producer -f producer/Dockerfile .
docker build -t ecoscape/object-classifier-data -f data/Dockerfile .
```

Load images into Minikube:

```bash
minikube image load ecoscape/object-classifier-consumer
minikube image load ecoscape/object-classifier-producer
minikube image load ecoscape/object-classifier-data
```

## Deploy with Helm

```bash
helm dependency update ./helm/object-classifier
helm upgrade --install object-classifier ./helm/object-classifier \
  -n object-classifier --create-namespace
```

## Common flags

Disable Strimzi dependency (if operator already exists):

```bash
helm upgrade --install object-classifier ./helm/object-classifier \
  -n object-classifier --create-namespace \
  --set strimzi.enabled=false
```

Disable Kafka + NodePools creation from this chart:

```bash
helm upgrade --install object-classifier ./helm/object-classifier \
  -n object-classifier --create-namespace \
  --set kafka.enabled=false \
  --set kafka.nodePools.enabled=false
```

## Runtime notes

- Producer data is extracted from `data/images.tar` by a producer initContainer.
- Producer and initContainer share the same Pod and PVC, so data is available at `/data/images`.
- Python logs are unbuffered by default (`PYTHONUNBUFFERED=1`) in producer and consumer.

## Verify

```bash
kubectl get pods -n object-classifier
kubectl get kafka -n object-classifier
kubectl get kafkanodepool -n object-classifier
kubectl get kafkatopic -n object-classifier
```

Consumer metrics:

```bash
kubectl port-forward -n object-classifier svc/object-classifier-consumer 5001:5001
```

Open `http://localhost:5001/metrics`.

## Cleanup

```bash
helm uninstall object-classifier -n object-classifier
kubectl delete namespace object-classifier
```
