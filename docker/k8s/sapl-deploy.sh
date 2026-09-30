#!/bin/bash

kubectl create namespace sapl
mkdir -p ./sapl-secret-data
kubectl -n sapl create secret generic sapl-secretkey --from-file=./sapl-secret-data/
kubectl apply -f sapl-k8s.yaml

kubectl rollout status deployment/sapl -n sapl

POD=$(kubectl get pod -n sapl -l app=sapl -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n sapl "$POD" -- ls -l /var/interlegis/sapl/data

