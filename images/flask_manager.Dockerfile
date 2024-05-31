FROM python:3.9-alpine

COPY manager /manager
WORKDIR /manager
ADD . /manager/

RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "/manager/run.py"]