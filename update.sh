git pull
docker stop talk
docker rm talk
docker build -t lanuage-talk-listen .
docker run --name talk -itd -p 4443:443 -v /opt/file:/opt/lanuage-talk-listen/file --restart=always lanuage-talk-listen
