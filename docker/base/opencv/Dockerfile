FROM dashcam-base02:1.0
MAINTAINER Kenjiro Mitsui <mitsui@inferret.co.uk>

RUN apt-get update && \
        apt-get install -y --no-install-recommends \
        cmake \
        yasm \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavformat-dev \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONIOENCODING "utf-8"

WORKDIR /
ENV OPENCV_VERSION="4.0.1"
RUN wget https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& rm ${OPENCV_VERSION}.zip \
&& wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& rm /${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& export LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:${LD_LIBRARY_PATH} \
&& cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D INSTALL_PYTHON_EXAMPLES=ON \
	-D INSTALL_C_EXAMPLES=OFF \
	-D OPENCV_ENABLE_NONFREE=ON \
	-D OPENCV_EXTRA_MODULES_PATH=/opencv_contrib-${OPENCV_VERSION}/modules \
	-D PYTHON_EXECUTABLE=$(which python3.6) \
        .. \
        #-D WITH_CUDA=ON \
	#-D BUILD_EXAMPLES=ON ..
#&& cmake -DBUILD_TIFF=ON \
#  -DBUILD_opencv_java=OFF \
#  -DOPENCV_EXTRA_MODULES_PATH=/opencv_contrib-${OPENCV_VERSION}/modules \
#  -DOPENCV_ENABLE_NONFREE=ON \
#  -DWITH_CUDA=ON \
#  -DWITH_OPENGL=ON \
#  -DWITH_OPENCL=ON \
#  -DWITH_IPP=ON \
#  -DWITH_TBB=ON \
#  -DWITH_EIGEN=ON \
#  -DWITH_V4L=ON \
#  -DBUILD_TESTS=OFF \
#  -DBUILD_PERF_TESTS=OFF \
#  -DCMAKE_BUILD_TYPE=RELEASE \
#  -DCMAKE_INSTALL_PREFIX=$(python3.6 -c "import sys; print(sys.prefix)") \
#  -DPYTHON_EXECUTABLE=$(which python3.6) \
#  -DPYTHON_INCLUDE_DIR=$(python3.6 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
#  -DPYTHON_PACKAGES_PATH=$(python3.6 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
#  ..
#  .. \
&& make -j install \
&& rm -r /opencv-${OPENCV_VERSION} \
&& rm -r /opencv_contrib-${OPENCV_VERSION}
