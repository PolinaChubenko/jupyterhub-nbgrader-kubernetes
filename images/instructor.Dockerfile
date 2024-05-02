FROM jupyter/minimal-notebook:hub-4.0.2
USER root
RUN apt-get update && apt install -y vim procps

# Install nbgrader and nbgrader-exchange release
RUN pip install nbgrader
RUN pip install https://github.com/PolinaChubenko/jupyterhub-nbgrader-kubernetes/releases/download/v0.0.1/nbgrader_k8s_exchange-0.0.1.tar.gz

# Install packages for python kernel
RUN pip install jiwer --no-cache-dir
RUN pip install gradio typing-extensions --no-cache-dir
RUN pip install torch torchvision --no-cache-dir
RUN pip install seaborn --no-cache-dir

# Setup nbgrader extensions
RUN jupyter server extension disable nbgrader.server_extensions.formgrader
RUN jupyter labextension disable nbgrader:formgrader
RUN jupyter labextension disable nbgrader:create-assignment

USER ${NB_USER}
