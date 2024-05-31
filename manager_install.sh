#!/bin/bash -e

kubectl delete deployment manager
kubectl delete service manager

eval $(minikube docker-env)
docker build -f images/flask_manager.Dockerfile -t flask-manager-sample:0.0.1 .
eval $(minikube docker-env -u)

kubectl create -f manager-configs/deployment.yaml
kubectl create -f manager-configs/service.yaml
kubectl get svc -o wide