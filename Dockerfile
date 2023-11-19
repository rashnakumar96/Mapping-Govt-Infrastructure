FROM python:3.9.7-slim
COPY . /

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean;

RUN java -jar scripts/browsermob-proxy-2.1.4/lib/browsermob-dist-2.1.4.jar --port 9090 &

RUN pip3 install git+https://github.com/cisagov/findcdn.git
RUN pip install -r requirements.txt

ENTRYPOINT ["/bin/sh"]