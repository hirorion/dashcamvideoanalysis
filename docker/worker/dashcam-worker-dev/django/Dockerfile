FROM python:3.6

ENV APP_PATH /opt/apps

#COPY startup.sh /root/
#RUN chmod 755 /root/startup.sh

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
#RUN chmod 755 /root/startup.sh \
RUN groupadd -g $APP_GROUP_ID devuser \
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

RUN git clone -b feature-irric git@gitlab:mitsui/DashCamAnalysisWeb.git feature-irric && \
    cd feature-irric && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR $APP_PATH/DashCamAnalysisWeb
