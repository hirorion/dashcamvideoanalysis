FROM dashcam-base01:1.0
LABEL maintainer="Kenjiro Mitsui <mitsui@inferret.co.uk>"

RUN apt-get update && \
        apt-get install -y --no-install-recommends \
        libssl-dev libbz2-dev libreadline-dev libsqlite3-dev \
        cpio && \
    rm -rf /var/lib/apt/lists/*

# pythonの環境準備
WORKDIR /root
RUN wget https://www.python.org/ftp/python/3.6.8/Python-3.6.8.tgz \
    && tar zxf Python-3.6.8.tgz \
    && cd Python-3.6.8 \
    && ./configure \
    && make altinstall \
    && cd .. \
    && rm -rf Python-3.6.8 \
    && rm -rf Python-3.6.8.tgz

ENV PYTHONIOENCODING "utf-8"

RUN pip3.6 --no-cache-dir install \
        Pillow \
        h5py \
        jupyter \
        keras_applications \
        keras_preprocessing \
        matplotlib \
        numpy \
        pandas \
        scipy \
        sklearn \
        wheel
#        && \
#    python -m ipykernel.kernelspec

# Configure the build for our CUDA configuration.
ENV CI_BUILD_PYTHON python3.6
ENV LD_LIBRARY_PATH /usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH
ENV TF_NEED_CUDA 1
ENV TF_NEED_TENSORRT 1
ENV TF_CUDA_COMPUTE_CAPABILITIES 6.1
ENV TF_CUDA_VERSION 9.0
ENV TF_CUDNN_VERSION 7
ENV TF_NEED_GCP 1
ENV TF_NEED_HDFS 1
ENV TF_NEED_OPENCL 0
ENV TF_NEED_JEMALLOC 0
ENV TF_ENABLE_XLA 0
ENV TF_NEED_VERBS 0
ENV TF_CUDA_CLANG 0
ENV TF_DOWNLOAD_CLANG 0
ENV TF_NEED_MKL 0
ENV TF_DOWNLOAD_MKL 0
ENV TF_NEED_MPI 0
ENV TF_NEED_S3 0
ENV TF_NEED_KAFKA 0
ENV TF_NEED_GDR 0
ENV TF_NEED_OPENCL_SYCL 0
ENV TF_SET_ANDROID_WORKSPACE 0
ENV TF_NEED_AWS 0
ENV TF_NEED_IGNITE 0
ENV TF_NEED_ROCM 0

# NCCL 2.x
ENV TF_NCCL_VERSION 2

# Download and build TensorFlow.
WORKDIR /tensorflow

RUN git clone --branch=r1.12 --depth=1 https://github.com/tensorflow/tensorflow.git . && \
    ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1 && \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:${LD_LIBRARY_PATH} tensorflow/tools/ci_build/builds/configured GPU \
    bazel build --verbose_failures --ignore_unsupported_sandboxing --config=opt --config=cuda -c opt --copt=-mavx --copt=-mavx2 --copt=-mfma --copt=-mfpmath=both --copt=-msse4.2 //tensorflow/tools/pip_package:build_pip_package && \
    bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/pip && \
    pip3.6 --no-cache-dir install --upgrade /tmp/pip/tensorflow-*.whl && \
    rm -rf /tmp/pip && \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:${LD_LIBRARY_PATH} tensorflow/tools/ci_build/builds/configured GPU \
    bazel build --verbose_failures --ignore_unsupported_sandboxing --config=opt --config=cuda -c opt --copt=-mavx --copt=-mavx2 --copt=-mfma --copt=-mfpmath=both --copt=-msse4.2 tensorflow:libtensorflow_cc.so && \
    install -m 0644 bazel-bin/tensorflow/libtensorflow_cc.so /usr/local/lib/libtensorflow_cc.so \
&& install -m 0644 bazel-bin/tensorflow/libtensorflow_framework.so /usr/local/lib/libtensorflow_framework.so \
&& HEADER_DIR=/usr/local/include/tensorflow \
&& mkdir -p $HEADER_DIR \
&& find tensorflow/core -follow -type f -name "*.h" | cpio -pdm $HEADER_DIR \
&& find tensorflow/cc   -follow -type f -name "*.h" | cpio -pdm $HEADER_DIR \
&& find tensorflow/c    -follow -type f -name "*.h" | cpio -pdm $HEADER_DIR \
&& find third_party/eigen3 -follow -type f | cpio -pdm $HEADER_DIR \
&& cd bazel-genfiles \
&& find tensorflow -follow -type f -name "*.h" | cpio -pdm $HEADER_DIR \
&& cd - \
&& cd bazel-tensorflow/external/protobuf_archive/src \
&& find google -follow -type f -name "*.h" | cpio -pdm $HEADER_DIR \
&& cd - \
&& cd bazel-tensorflow/external/eigen_archive \
&& find Eigen       -follow -type f | cpio -pdm $HEADER_DIR \
&& find unsupported -follow -type f | cpio -pdm $HEADER_DIR \
&& cd - \
&& ./tensorflow/contrib/makefile/download_dependencies.sh \
&& cd tensorflow/contrib/makefile/downloads \
&& cp -pr absl/absl $HEADER_DIR \
&& cd - \
&& rm -rf /root/.cache \
&& rm -rf tensorflow
# Clean up pip wheel and Bazel cache when done.

WORKDIR /root
