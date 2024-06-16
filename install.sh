#!/bin/bash -e

# Create a brand new minikube environment. Skip this if you already have a cluster.
minikube delete || true
minikube start --vm-driver=docker

# Build custom docker images
eval $(minikube docker-env)
docker build -f images/student.Dockerfile -t nbgrader-student-sample:0.0.1 .
docker build -f images/instructor.Dockerfile -t nbgrader-instructor-sample:0.0.1 .
docker build -f images/hub.Dockerfile -t nbgrader-hub-sample:0.0.1 .
docker build -f images/flask_manager.Dockerfile -t flask-manager-sample:0.0.1 .
eval $(minikube docker-env -u)

# Update dependencies and install the chart
helm dependency update nbgrader-chart
helm install nbgrader nbgrader-chart -f nbgrader-chart/values.yaml \
    --set-file jupyterhub.hub.extraFiles.courses_management.stringData=./extra_files/courses_management.py \
    --set-file jupyterhub.hub.extraFiles.settings.stringData=./extra_files/settings.py \
    --set-file jupyterhub.hub.extraFiles.accessible_services.stringData=./extra_files/accessible_services.py \
    --set-file jupyterhub.hub.extraFiles.courses_info_json.stringData=./extra_files/courses_info.json \
    --set-file jupyterhub.hub.extraFiles.students_info_json.stringData=./extra_files/students_info.json 

# We're done!
kubectl get pods
minikube service list