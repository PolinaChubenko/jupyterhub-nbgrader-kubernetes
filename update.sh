#!/bin/bash -e

helm dependency update nbgrader-chart
helm upgrade -i nbgrader nbgrader-chart -f nbgrader-chart/values.yaml

# We're done!
kubectl get pods
minikube service list