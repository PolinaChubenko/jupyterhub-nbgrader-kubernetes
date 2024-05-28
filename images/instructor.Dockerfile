FROM quay.io/jupyter/minimal-notebook:hub-4.1.3
USER root
RUN apt-get update && apt install -y vim procps

# Install nbgrader and nbgrader-exchange release
RUN pip install nbgrader==0.9.2
COPY nbgrader-exchange/dist/nbgrader_k8s_exchange-0.0.1-py3-none-any.whl /
RUN pip install /nbgrader_k8s_exchange-0.0.1-py3-none-any.whl

# Install packages for python kernel
RUN pip install jiwer --no-cache-dir
RUN pip install gradio typing-extensions --no-cache-dir
# RUN pip install torch torchvision --no-cache-dir
RUN pip install seaborn --no-cache-dir

# Setup nbgrader extensions
RUN jupyter server extension disable nbgrader.server_extensions.formgrader
RUN jupyter labextension disable nbgrader:formgrader
RUN jupyter labextension disable nbgrader:create-assignment

USER ${NB_USER}
