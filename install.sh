#!/bin/bash -e

# Create a brand new minikube environment. Skip this if you already have a cluster.
minikube delete || true
minikube start --vm-driver=docker

# Build custom docker images
eval $(minikube docker-env)
docker build -f images/student.Dockerfile -t nbgrader-student-sample:0.0.1 .
docker build -f images/instructor.Dockerfile -t nbgrader-instructor-sample:0.0.1 .
docker build -f images/hub.Dockerfile -t nbgrader-hub-sample:0.0.1 .
eval $(minikube docker-env -u)

# Update dependencies and install the chart
helm dependency update nbgrader-chart
helm install nbgrader nbgrader-chart -f nbgrader-chart/values.yaml

# We're done!
kubectl get pods
minikube service list