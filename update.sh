#!/bin/bash -e

helm dependency update nbgrader-chart
helm upgrade -i nbgrader nbgrader-chart -f nbgrader-chart/values.yaml \
    --set-file jupyterhub.hub.extraFiles.courses_management.stringData=./extra_files/courses_management.py \
    --set-file jupyterhub.hub.extraFiles.settings.stringData=./extra_files/settings.py \
    --set-file jupyterhub.hub.extraFiles.accessible_services.stringData=./extra_files/accessible_services.py \
    --set-file jupyterhub.hub.extraFiles.courses_info_json.stringData=./extra_files/courses_info.json


# We're done!
kubectl get pods
minikube service list