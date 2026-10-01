FROM golang:1.26.0 AS builder

RUN go install go.k6.io/xk6/cmd/xk6@v1.3.5

RUN xk6 build \
      --with github.com/mostafa/xk6-kafka@v1.3.0 \
      --with github.com/szkiba/xk6-prometheus@v0.3.0 \
      --output /k6

# grafana/xk6-kafka imports go.k6.io/k6/v2, a different
# module path than the k6 v1 binary, so its init() registers into a registry the
# binary never reads and "k6/x/kafka" stays unknown at runtime.
RUN printf 'import "k6/x/kafka";\nexport default function () {}\n' > /tmp/check.js \
    && K6_BINARY_PROVISIONING=false /k6 archive /tmp/check.js -O /tmp/check.tar \
    && /k6 version | grep -q 'xk6-prometheus'

FROM alpine:3.19

# ca-certificates for TLS (Kafka / Prometheus endpoints)
RUN apk add --no-cache ca-certificates

COPY --from=builder /k6 /usr/bin/k6
COPY script.js /app/script.js
COPY images.tar /tmp/images.tar

RUN mkdir -p /data/images \
    && tar -xf /tmp/images.tar -C /data/images --strip-components=1 \
    && find /data/images -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) | sort | awk -F/ '{ folder = $(NF - 1); if (++count[folder] <= 3) print }' > /app/image-files.list \
    && tr '\n' ',' < /app/image-files.list | sed 's/,$//' > /app/image-files.csv \
    && rm -f /tmp/images.tar

ENV K6_BINARY_PROVISIONING=false
ENV IMAGE_FILES_CSV_PATH=/app/image-files.csv

ENTRYPOINT ["k6"]
CMD ["run", "/app/script.js"]
