FROM jupyterhub/k8s-hub:3.0.3
USER root

RUN apt update && apt install vim procps fakeroot gcc -y

# Install nbgrader-exchange release
RUN pip install nbgrader==0.9.2
COPY nbgrader-exchange/dist/nbgrader_k8s_exchange-0.0.1-py3-none-any.whl /
RUN pip install /nbgrader_k8s_exchange-0.0.1-py3-none-any.whl

# Install packages for python kernel
RUN pip install jiwer --no-cache-dir
RUN pip install gradio typing-extensions --no-cache-dir
# RUN pip install torch torchvision --no-cache-dir
RUN pip install seaborn --no-cache-dir

# Setup nbgrader extensions
RUN jupyter server extension disable nbgrader.server_extensions.assignment_list
RUN jupyter server extension disable nbgrader.server_extensions.course_list
RUN jupyter labextension disable nbgrader:assignment-list
RUN jupyter labextension disable nbgrader:course-list

USER jovyan
