{{- define "object-classifier.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "object-classifier.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := include "object-classifier.name" . -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "object-classifier.namespace" -}}
{{- .Release.Namespace -}}
{{- end -}}

{{- define "object-classifier.labels" -}}
app.kubernetes.io/name: {{ include "object-classifier.name" . }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "object-classifier.kafkaBootstrapService" -}}
{{- printf "%s-kafka-bootstrap.%s.svc.cluster.local:9092" .Values.kafka.name (include "object-classifier.namespace" .) -}}
{{- end -}}

{{- define "object-classifier.consumerImage" -}}
{{- printf "%s" .Values.consumer.image.repository -}}
{{- end -}}

{{- define "object-classifier.producerImage" -}}
{{- printf "%s" .Values.producer.image.repository -}}
{{- end -}}

{{- define "object-classifier.producerInitImage" -}}
{{- printf "%s" .Values.producer.initImage.repository -}}
{{- end -}}
