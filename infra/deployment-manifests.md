# Infrastructure & Deployment Sketch

Knowledge Harvest is designed for cloud‑native deployment.  Each microservice runs in its own container and communicates over HTTP or asynchronous messaging.  A Kubernetes cluster orchestrates the containers and provides scaling, resilience and service discovery.

## Components

* **API Gateway:** Routes external requests to the appropriate microservice and handles authentication.
* **Capture Service Deployment:** Handles upload of raw video.  Scaled based on CPU and I/O.
* **Transcription & Summarisation Services:** These stateless services are GPU/CPU intensive; autoscaling policies should be configured according to queue length.
* **Knowledge‑Indexer & Search Services:** Stateful services backed by a database (e.g. PostgreSQL or Elasticsearch) and object storage (e.g. S3 compatible).
* **Message Broker:** (e.g. RabbitMQ or Kafka) decouples processing steps between capture, transcription and summarisation.

## Sample Kubernetes manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: capture-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: capture-service
  template:
    metadata:
      labels:
        app: capture-service
    spec:
      containers:
        - name: capture-service
          image: your-registry/capture-service:latest
          env:
            - name: STORAGE_BUCKET
              value: knowledge-harvest-recordings
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: capture-service
spec:
  selector:
    app: capture-service
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

The same pattern applies for other services.  Helm charts or Kustomize overlays can be used to manage environments (dev, staging, production).  Secrets (API keys, database credentials) should be stored in Kubernetes secrets or a cloud secret manager.

Deployment pipelines (e.g. GitHub Actions) can build images, run tests and apply manifests to the cluster.