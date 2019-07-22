#===================================================
# development
#===================================================
FROM dashcam-base-dev:1.0 as development
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
  && dpkg-reconfigure -f noninteractive tzdata \
  && apt-get update \
  && apt-get install -y --no-install-recommends ssh less vim sudo \
  && rm -rf /var/lib/apt/lists/*

# 指定ユーザーをセット
# docker --build-argでセットされたこの変数のIDが使われる。
# ホストのIDと同じにするとそのIDでプロセスが実行される
# devuser mapping group id
ARG APP_GROUP_ID=60001
# ai process mapping user id
ARG APP_USER_ID=60001
# ai process mapping user name
ARG APP_USER_NAME=edw

COPY startup.sh /root/
COPY launch_docker.sh /usr/local/bin

# ホームディレクトリ作成
RUN chmod 755 /root/startup.sh && chmod 755 /usr/local/bin/launch_docker.sh \
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

USER $APP_USER_NAME
WORKDIR /home/$APP_USER_NAME
RUN cd .ssh && \
  echo "Host gitlab\n\
    HostName inferret.net\n\
    Port 49322\n\
    User $APP_USER_NAME\n\
    StrictHostKeyChecking no\n\
    IdentityFile ~/.ssh/id_rsa_dashcam_docker" > config && \
  cd - && \
  # for compile trancking
  echo "export LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs" >> .bashrc && \
  ln -s /usr/local/include . && \
  ln -s /usr/local/lib .

RUN git clone -b feature-windows git@gitlab:mitsui/speechaccounts_rabbitmq.git feature-windows && \
  cd feature-windows && \
  git config core.sparsecheckout true && \
  git config --global push.default matching && \
  echo tracking > .git/info/sparse-checkout && \
  git read-tree -m -u HEAD && \
  cd tracking && \
  mkdir linux && \
  cd linux && \
  cmake .. && \
  env LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs make -j && \
  cd - && \
  cd - && \
  cd -

# これしか実行させない場合にENTRYPOINT
USER root
RUN  cp /home/$APP_USER_NAME/feature-windows/tracking/linux/trackingGlobalFullMatchTFClasses /usr/local/bin
# docker run で指定した-e CUR_USER_NAMEでbashが実行される
ENTRYPOINT ["/root/startup.sh"]

#===================================================
# production
#===================================================

FROM nvidia/cuda:9.0-base-ubuntu16.04 as production
MAINTAINER Kenjiro Mitsui <mitsui@inferret.co.uk>

WORKDIR /root

RUN apt-get update && apt-get install -y --no-install-recommends \
    libswscale-dev \
    libtbb2 \
    libtbb-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavformat-dev \
    libcudnn7=7.2.1.38-1+cuda9.0 && \
    #libnccl2=2.2.13-1+cuda9.0 && \
    #apt-get install -y --no-install-recommends nvinfer-runtime-trt-repo-ubuntu1604-4.0.1-ga-cuda9.0 && \
    #apt-get update && \
    #apt-get install -y --no-install-recommends libnvinfer4=4.1.2-1+cuda9.0 && \
    rm -rf /var/lib/apt/lists/*
    #find /usr/local/cuda-9.0/lib64/ -type f -name 'lib*_static.a' -not -name 'libcudart_static.a' -delete
    #rm /usr/lib/x86_64-linux-gnu/libcudnn_static_v7.a

# Link NCCL libray and header where the build script expects them.
#RUN mkdir /usr/local/cuda-9.0/lib &&  \
    #ln -s /usr/lib/x86_64-linux-gnu/libnccl.so.2 /usr/local/cuda/lib/libnccl.so.2
    #ln -s /usr/include/nccl.h /usr/local/cuda/include/nccl.h

ENV TZ Asia/Tokyo
RUN apt-get update \
  && apt-get install -y tzdata \
  && rm -rf /var/lib/apt/lists/* \
  && echo "${TZ}" > /etc/timezone \
  && rm /etc/localtime \
  && ln -s /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
  && dpkg-reconfigure -f noninteractive tzdata \
  && apt-get update \
  && apt-get install -y --no-install-recommends less vim sudo \
  && rm -rf /var/lib/apt/lists/*

# 指定ユーザーをセット
# docker-compose.xmlでセットされたこの変数のIDが使われる。
# ホストのIDと同じにするとそのIDでプロセスが実行される
# devuser mapping group id
ARG APP_GROUP_ID=60001
# ai process mapping user id
ARG APP_USER_ID=60001
# ai process mapping user name
ARG APP_USER_NAME=edw

COPY startup.sh /root/
COPY launch_docker.sh /usr/local/bin

# ホームディレクトリ作成
RUN chmod 755 /root/startup.sh && chmod 755 /usr/local/bin/launch_docker.sh \
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

USER $APP_USER_NAME
WORKDIR /home/$APP_USER_NAME
RUN cd .ssh && \
  echo "Host gitlab\n\
    HostName inferret.net\n\
    Port 49322\n\
    User $APP_USER_NAME\n\
    StrictHostKeyChecking no\n\
    IdentityFile ~/.ssh/id_rsa_dashcam_docker" > config && \
  cd - && \
  # for executeing trancking
  echo "export LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:/usr/local/lib" >> .bashrc

# 必要なライブラリをdevelopmentからコピー
COPY --from=development /usr/local/lib/libtensorflow_cc.so /usr/local/lib
COPY --from=development /usr/local/lib/libtensorflow_framework.so /usr/local/lib
COPY --from=development /usr/local/cuda-9.0/targets/x86_64-linux/lib/libcublas.so.9.0 /usr/local/lib
COPY --from=development /usr/local/cuda-9.0/targets/x86_64-linux/lib/libcusolver.so.9.0 /usr/local/lib
COPY --from=development /usr/local/cuda-9.0/targets/x86_64-linux/lib/libcudart.so.9.0 /usr/local/lib
COPY --from=development /usr/local/cuda-9.0/targets/x86_64-linux/lib/libcufft.so.9.0 /usr/local/lib
COPY --from=development /usr/local/cuda-9.0/targets/x86_64-linux/lib/libcurand.so.9.0 /usr/local/lib
COPY --from=development /usr/local/cuda/lib64/stubs/libcuda.so.1 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_video.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_ximgproc.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_flann.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_features2d.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_optflow.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_dnn.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_calib3d.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_videoio.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_imgcodecs.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_imgproc.so.4.0 /usr/local/lib
COPY --from=development /usr/local/lib/libopencv_core.so.4.0 /usr/local/lib
COPY --from=development /usr/lib/x86_64-linux-gnu/libgomp.so.1 /usr/local/lib
COPY --from=development /home/$APP_USER_NAME/feature-windows/tracking/linux/trackingGlobalFullMatchTFClasses /usr/local/bin

# これしか実行させない場合にENTRYPOINT
USER root
# docker run で指定した-e CUR_USER_NAMEでbashが実行される
ENTRYPOINT ["/root/startup.sh"]
