# ObjectClassifier Helm Chart

This chart deploys ObjectClassifier workloads and can optionally install Strimzi as a dependency.

## Features

- All resources in one namespace (the Helm release namespace)
- Optional Strimzi operator dependency via `strimzi.enabled`
- Optional Strimzi `Kafka` resource via `kafka.enabled`
- Optional Strimzi `KafkaNodePool` resources via `kafka.nodePools.enabled`
- Optional `KafkaTopic` resources via `topics.enabled`
- Image extraction via producer initContainer (same Pod/Node as producer)
- Optional image PVC

## Prerequisites

- Helm 3.x
- Kubernetes cluster
- Strimzi CRDs available when `kafka.enabled=true` (either via dependency or pre-installed operator)

## Install

```bash
helm dependency update ./helm/object-classifier
helm upgrade --install object-classifier ./helm/object-classifier -n object-classifier --create-namespace
```

All chart resources are always created in the namespace passed via `-n/--namespace`.

## Common toggles

Disable Strimzi dependency (use already installed operator):

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

Only disable NodePools while keeping Kafka resource enabled:

```bash
helm upgrade --install object-classifier ./helm/object-classifier \
  -n object-classifier --create-namespace \
  --set kafka.nodePools.enabled=false
```
