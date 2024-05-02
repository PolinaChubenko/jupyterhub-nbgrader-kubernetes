FROM jupyterhub/k8s-hub:3.0.3
USER root

RUN apt update && apt install vim procps fakeroot gcc -y

# Install nbgrader-exchange release
RUN pip install nbgrader
RUN pip install https://github.com/PolinaChubenko/jupyterhub-nbgrader-kubernetes/releases/download/v0.0.1/nbgrader_k8s_exchange-0.0.1.tar.gz

# Install packages for python kernel
RUN pip install jiwer --no-cache-dir
RUN pip install gradio typing-extensions --no-cache-dir
RUN pip install torch torchvision --no-cache-dir
RUN pip install seaborn --no-cache-dir

# Setup nbgrader extensions
RUN jupyter server extension disable nbgrader.server_extensions.assignment_list
RUN jupyter server extension disable nbgrader.server_extensions.course_list
RUN jupyter labextension disable nbgrader:assignment-list
RUN jupyter labextension disable nbgrader:course-list

USER jovyan
