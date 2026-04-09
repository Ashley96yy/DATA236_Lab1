# Lab 2 Kubernetes Deployment

This folder contains a single-namespace Kubernetes starter setup for Lab 2.

## What Is Included

- `mongodb` via StatefulSet
- `zookeeper` and `kafka`
- `mongo-init` Job for bootstrap + demo seed
- `user-service`
- `owner-service`
- `restaurant-service`
- `review-api-service`
- `review-worker-service`
- `api-gateway`
- `frontend`

## Before Applying

1. Build and push the images you want Kubernetes to use.
2. Replace the image values in the manifests if you are deploying to AWS/EKS.
3. Edit `secret-template.yaml` with your real non-demo values before applying.

Default image names in these manifests use the current local Docker tags:

- `lab1-user-service:latest`
- `lab1-owner-service:latest`
- `lab1-restaurant-service:latest`
- `lab1-review-api-service:latest`
- `lab1-review-worker-service:latest`
- `lab1-mongo-init:latest`
- `lab1-frontend:latest`

For AWS, replace them with your ECR image URIs.

## Apply Order

```bash
kubectl apply -k deploy/k8s
```

## Validate

```bash
kubectl get pods -n yelp-lab2
kubectl get svc -n yelp-lab2
kubectl logs job/mongo-init -n yelp-lab2
```

## AWS Notes

- If you expose both `frontend` and `api-gateway` as `LoadBalancer`, you will get separate public endpoints.
- For the cleanest frontend behavior in AWS, rebuild the frontend image with:

```bash
docker build --build-arg VITE_API_BASE_URL=/api/v1 -t <your-frontend-image> ./frontend
```

That works best when you later place frontend and gateway behind the same ingress or reverse proxy.

## Suggested AWS Screenshots

- `kubectl get pods -n yelp-lab2`
- `kubectl get svc -n yelp-lab2`
- MongoDB pod running
- Kafka pod running
- frontend reachable
- gateway reachable
