FROM ubuntu:16.04
MAINTAINER Yu You <youyu.youyu@gmail.com>

# old one is 2.4.11
ENV OPENCV 3.1.0

# Enable the Ubuntu multiverse repository.
#RUN echo "deb http://us.archive.ubuntu.com/ubuntu/ trusty multiverse" >> /etc/apt/source.list
#RUN echo "deb-src http://us.archive.ubuntu.com/ubuntu/ trusty multiverse">> /etc/apt/source.list
#RUN echo "deb http://us.archive.ubuntu.com/ubuntu/ trusty-updates multiverse" >> /etc/apt/source.list
#RUN echo "deb-src http://us.archive.ubuntu.com/ubuntu/ trusty-updates multiverse" >> /etc/apt/source.list
# Initial update and install of dependency that can add apt-repos
RUN apt-get -y update && apt-get install -y software-properties-common python-software-properties

# Add global apt repos
RUN add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu precise universe" && \
    add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu precise main restricted universe multiverse" && \
    add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu precise-updates main restricted universe multiverse" && \
    add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu precise-backports main restricted universe multiverse"

# Get dependencies
RUN apt-get update && apt-get install -y \
    libgtk2.0-dev \
    libjpeg-dev \
    libjasper-dev \
    libopenexr-dev cmake python-dev \
    python-numpy python-tk libtbb-dev \
    libeigen2-dev yasm libfaac-dev \
    libopencore-amrnb-dev libopencore-amrwb-dev \
    libtheora-dev libvorbis-dev libxvidcore-dev \
    libx264-dev libqt4-dev libqt4-opengl-dev \
    sphinx-common libv4l-dev libdc1394-22-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libglew-dev libboost-dev libboost-python-dev libboost-serialization-dev \
    htop nano wget git unzip \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN cd /opt && wget http://bitbucket.org/eigen/eigen/get/3.2.10.tar.gz -O eigen3.tgz \
&& tar zxvf eigen3.tgz && cd  eigen-eigen-b9cd8366d4e8 \
&& mkdir build && cd build \
&& cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=RELEASE .. \
&& make install \
&& cd /opt && git clone https://github.com/stevenlovegrove/Pangolin.git \
&& cd Pangolin && mkdir build && cd build && cmake  .. \
&& make -j4 && make install \
&& cd /opt && wget https://codeload.github.com/opencv/opencv/zip/$OPENCV -O opencv.zip \
&& unzip opencv.zip \
&& cd opencv-$OPENCV && mkdir build && cd build \
&& cmake -D CMAKE_BUILD_TYPE=RELEASE -D WITH_CUDA=OFF -D WITH_OPENGL=OFF .. \
&& make -j4 && make install \
&& rm -rf /opt/* && ldconfig

RUN git clone https://github.com/raulmur/ORB_SLAM2.git ORB_SLAM2 \
&& cd ORB_SLAM2 \
&& ./build.sh
