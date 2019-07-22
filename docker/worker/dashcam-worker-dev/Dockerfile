FROM ubuntu:18.04 as development
MAINTAINER Kenjiro Mitsui <mitsui@inferret.co.uk>

WORKDIR /root

# パッケージ取得先のミラーをjaistに変更する
RUN sed -i.bak -e "s%http://archive.ubuntu.com/ubuntu/%http://ftp.jaist.ac.jp/pub/Linux/ubuntu/%g" /etc/apt/sources.list

ENV TZ Asia/Tokyo
RUN apt-get update \
  && apt-get install -y tzdata \
  && rm -rf /var/lib/apt/lists/* \
  && echo "${TZ}" > /etc/timezone \
  && rm /etc/localtime \
  && ln -s /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
  && dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update && \
        apt-get install -y --no-install-recommends \
        curl git ssh less vim sudo \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 --no-cache-dir install virtualenv

COPY startup.sh /root/
RUN chmod 755 /root/startup.sh

# 指定ユーザーをセット
# docker --build-argでセットされたこの変数のIDが使われる。
# ホストのIDと同じにするとそのIDでプロセスが実行される
# devuser mapping group id
ARG APP_GROUP_ID=60001
# ai process mapping user id
ARG APP_USER_ID=60001
# ai process mapping user name
ARG APP_USER_NAME=mitsui

# ホームディレクトリ作成
RUN chmod 755 /root/startup.sh \
  && groupadd -g $APP_GROUP_ID devuser \
  && useradd $APP_USER_NAME -u $APP_USER_ID -g $APP_GROUP_ID -m \
  && chmod g+rwxs /home/$APP_USER_NAME \
  && echo "$APP_USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# $APP_USER_NAME 初期設定
USER $APP_USER_NAME
WORKDIR /home/$APP_USER_NAME
COPY id_rsa_dashcam_docker .ssh/

# 一旦rootで変更
USER root
RUN chown -R $APP_USER_NAME:devuser .ssh && chmod 700 .ssh && chmod 400 .ssh/id_rsa_dashcam_docker

# ユーザー初期設定
USER $APP_USER_NAME
WORKDIR /home/$APP_USER_NAME
RUN cd .ssh && \
  echo "Host gitlab\n\
    HostName inferret.net\n\
    Port 49322\n\
    User $APP_USER_NAME\n\
    StrictHostKeyChecking no\n\
    IdentityFile ~/.ssh/id_rsa_dashcam_docker" > config && \
  cd -

RUN git clone -b feature-irric git@gitlab:mitsui/DashCamAnalysisWeb.git feature-irric
RUN virtualenv --python=python3 --system-site-packages venv

RUN echo 'source venv/bin/activate' >> ~/.bashrc
RUN cd feature-irric && \
  ~/venv/bin/pip3 install -r requirements_worker.txt && \
  cd -

USER root
WORKDIR /tmp
RUN curl -fsSL https://get.docker.com/builds/Linux/x86_64/docker-latest.tgz > docker.tgz \
  && tar xfz docker.tgz docker/docker \
  && mv docker/docker /usr/local/bin/docker \
  && rm -rf docker \
  && chmod +x /usr/local/bin/docker

# これしか実行させない場合にENTRYPOINT
USER root
# docker run で指定した-e CUR_USER_NAMEでbashが実行される
ENTRYPOINT ["/root/startup.sh"]
