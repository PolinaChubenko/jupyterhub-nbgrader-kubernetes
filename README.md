# jupyterhub-nbgrader-kubernetes

## Instalation from scatch

### Helm
Installing [helm](https://helm.sh/docs/intro/install/)

```
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
sudo apt-get install apt-transport-https --yes
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

### kubectl
Installing [kubectl binary with curl on Linux](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)

Download the latest release with the command:
```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```
Download the kubectl checksum file:
```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
```

Validate the kubectl binary against the checksum file:
```
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check
```

If valid, the output is:
```
kubectl: OK
```

Install kubectl
```
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

Test to ensure the version you installed is up-to-date:
```
kubectl version --client
```

### Minikube
Installing [Minikube](https://kubernetes.io/ru/docs/tasks/tools/install-minikube/)

```
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 \
  && chmod +x minikube
```

To make Minikube executable file accessible from any directory, run the following commands::
```
sudo mkdir -p /usr/local/bin/
sudo install minikube /usr/local/bin/
```

### Кластеры и kubectl
If you are using kubectl to work with multiple clusters, make sure you select the correct context:
```
kubectl config get-contexts
CURRENT   NAME          CLUSTER       AUTHINFO      NAMESPACE
          kind-kind     kind-kind     kind-kind     
*         kind-kind-2   kind-kind-2   kind-kind-2
```
The asterisk means that we are connected to the kind-kind-2 cluster
To switch to another cluster, enter: `kubectl config use-context kind-kind`  


## Start k8s cluster and run JupyterHub with nbgrader
Basically, there are 2 bash scripts:
- `install.sh` that starts cluster with all the setup (run at the begining)
- `update.sh` that updates nbgrader-chart (run after changing values.yaml)

### First run
Do
```
chmod +x install.sh
./install.sh
```
After instalation we need to make our cluster accessable externally. 
As in values.yaml we say cluster to be deployed on port 30080, use nginx and set the following
```
proxy_pass http://192.168.49.2:30080;
```
