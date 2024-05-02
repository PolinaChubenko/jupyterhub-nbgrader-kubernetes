FROM jupyterhub/k8s-hub:3.0.3
USER root

RUN apt update && apt install vim procps fakeroot gcc -y

# Install nbgrader-exchange release
RUN pip install nbgrader https://github.com/PolinaChubenko/jupyterhub-nbgrader-kubernetes/releases/download/v0.0.1/nbgrader_k8s_exchange-0.0.1.tar.gz

# Setup nbgrader extensions
RUN jupyter server extension disable nbgrader.server_extensions.assignment_list
RUN jupyter server extension disable nbgrader.server_extensions.course_list
RUN jupyter labextension disable nbgrader:assignment-list
RUN jupyter labextension disable nbgrader:course-list

USER jovyan
