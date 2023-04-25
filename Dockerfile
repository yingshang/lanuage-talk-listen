FROM ubuntu:20.04

RUN apt update -y
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN apt install -y python3 python3-pip python3-dev nginx ffmpeg
RUN cd /root &&  openssl rand -writerand .rnd
RUN cd /opt && openssl genrsa -out server.key 2048   &&  openssl req -new -key server.key -out server.csr --batch && openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
COPY . /opt/feishu-talk
COPY nginx.conf /etc/nginx/

WORKDIR /opt/feishu-talk

ENTRYPOINT nginx &&  python3 app.py
