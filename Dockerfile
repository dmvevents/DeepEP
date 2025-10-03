ARG CUDA_VERSION=12.9.1 # https://docs.nvidia.com/deeplearning/frameworks/pytorch-release-notes/rel-25-06.html#rel-25-06
FROM nvcr.io/nvidia/pytorch:25.06-py3

# ===== SM90-only (H200/Hopper) build targets ==================================
# Force Hopper-only codegen everywhere (CMake, nvcc, PyTorch extensions).
# PTX for compute_90 is embedded for forward-compat JIT within Hopper family.
ENV CUDAARCHS=90 \
    CMAKE_CUDA_ARCHITECTURES=90 \
    TORCH_CUDA_ARCH_LIST=9.0+PTX \
    FORCE_CUDA=1 \
    GENCODE_FLAGS="-gencode=arch=compute_90,code=sm_90 -gencode=arch=compute_90,code=compute_90" \
    NVCC_GENCODE="-gencode=arch=compute_90,code=sm_90 -gencode=arch=compute_90,code=compute_90" \
    NVCCFLAGS="-gencode=arch=compute_90,code=sm_90 -gencode=arch=compute_90,code=compute_90" \
    CUDAFLAGS="-gencode=arch=compute_90,code=sm_90 -gencode=arch=compute_90,code=compute_90"
# ==============================================================================

ARG GDRCOPY_VERSION=v2.4.4
ARG EFA_INSTALLER_VERSION=1.42.0
ARG AWS_OFI_NCCL_VERSION=v1.16.0
ARG NCCL_VERSION=v2.27.5-1
ARG NCCL_TESTS_VERSION=v2.16.4
ARG NVSHMEM_VERSION=3.2.5-1

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get remove -y --allow-change-held-packages \
    ibverbs-utils \
    libibverbs-dev \
    libibverbs1 \
    libmlx5-1 \
    libnccl2 \
    libnccl-dev

# Keep HPC-X/UCX so PyTorch can load libucs.so.0 at import time.
# We will NOT use HPC-X's MPI; PATH stays pointed at /opt/amazon/openmpi.
RUN test -d /opt/hpcx/ucx/lib && echo "/opt/hpcx/ucx/lib" > /etc/ld.so.conf.d/hpcx-ucx.conf || true \
    && ldconfig

ENV OPAL_PREFIX=

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --allow-unauthenticated \
    apt-utils \
    autoconf \
    automake \
    build-essential \
    check \
    cmake \
    curl \
    debhelper \
    devscripts \
    git \
    gcc \
    gdb \
    kmod \
    libsubunit-dev \
    libtool \
    openssh-client \
    openssh-server \
    pkg-config \
    vim
RUN apt-get purge -y cuda-compat-*

RUN mkdir -p /var/run/sshd
RUN sed -i 's/[ #]\(.*StrictHostKeyChecking \).*/ \1no/g' /etc/ssh/ssh_config && \
    echo "    UserKnownHostsFile /dev/null" >> /etc/ssh/ssh_config && \
    sed -i 's/#\(StrictModes \).*/\1no/g' /etc/ssh/sshd_config

ENV LD_LIBRARY_PATH /usr/local/cuda/extras/CUPTI/lib64:/opt/amazon/openmpi/lib:/opt/nccl/build/lib:/opt/amazon/efa/lib:/opt/aws-ofi-nccl/install/lib:/usr/local/lib:$LD_LIBRARY_PATH
ENV PATH /opt/amazon/openmpi/bin/:/opt/amazon/efa/bin:/usr/bin:/usr/local/bin:$PATH

RUN curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
    && python3 /tmp/get-pip.py \
    && pip3 install awscli pynvml

#################################################
## Install NVIDIA GDRCopy
##
## NOTE: if `nccl-tests` or `/opt/gdrcopy/bin/sanity -v` crashes with incompatible version, ensure
## that the cuda-compat-xx-x package is the latest.
RUN git clone -b ${GDRCOPY_VERSION} https://github.com/NVIDIA/gdrcopy.git /tmp/gdrcopy \
    && cd /tmp/gdrcopy \
    && make prefix=/opt/gdrcopy install

ENV LD_LIBRARY_PATH /opt/gdrcopy/lib:$LD_LIBRARY_PATH
ENV LIBRARY_PATH /opt/gdrcopy/lib:$LIBRARY_PATH
ENV CPATH /opt/gdrcopy/include:$CPATH
ENV PATH /opt/gdrcopy/bin:$PATH

#################################################
## Install EFA installer
RUN cd $HOME \
    && curl -O https://efa-installer.amazonaws.com/aws-efa-installer-${EFA_INSTALLER_VERSION}.tar.gz \
    && tar -xf $HOME/aws-efa-installer-${EFA_INSTALLER_VERSION}.tar.gz \
    && cd aws-efa-installer \
    && ./efa_installer.sh -y -g -d --skip-kmod --skip-limit-conf --no-verify \
    && rm -rf $HOME/aws-efa-installer

###################################################
## Install NCCL (SM90-only)
RUN git clone -b ${NCCL_VERSION} https://github.com/NVIDIA/nccl.git  /opt/nccl \
    && cd /opt/nccl \
    && make -j $(nproc) src.build CUDA_HOME=/usr/local/cuda NVCC_GENCODE="${GENCODE_FLAGS}"

###################################################
## Install AWS-OFI-NCCL plugin
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libhwloc-dev
#Switch from sh to bash to allow parameter expansion
SHELL ["/bin/bash", "-c"]
RUN curl -OL https://github.com/aws/aws-ofi-nccl/releases/download/${AWS_OFI_NCCL_VERSION}/aws-ofi-nccl-${AWS_OFI_NCCL_VERSION//v}.tar.gz \
    && tar -xf aws-ofi-nccl-${AWS_OFI_NCCL_VERSION//v}.tar.gz \
    && cd aws-ofi-nccl-${AWS_OFI_NCCL_VERSION//v} \
    && ./configure --prefix=/opt/aws-ofi-nccl/install \
        --with-mpi=/opt/amazon/openmpi \
        --with-libfabric=/opt/amazon/efa \
        --with-cuda=/usr/local/cuda \
        --enable-platform-aws \
    && make -j $(nproc) \
    && make install \
    && cd .. \
    && rm -rf aws-ofi-nccl-${AWS_OFI_NCCL_VERSION//v} \
    && rm aws-ofi-nccl-${AWS_OFI_NCCL_VERSION//v}.tar.gz

SHELL ["/bin/sh", "-c"]

###################################################
## Install NCCL-tests (SM90-only)
RUN git clone -b ${NCCL_TESTS_VERSION} https://github.com/NVIDIA/nccl-tests.git /opt/nccl-tests \
    && cd /opt/nccl-tests \
    && make -j $(nproc) \
        MPI=1 \
        MPI_HOME=/opt/amazon/openmpi/ \
        CUDA_HOME=/usr/local/cuda \
        NCCL_HOME=/opt/nccl/build \
        NVCC_GENCODE="${GENCODE_FLAGS}"

RUN rm -rf /var/lib/apt/lists/*

## Set Open MPI variables to exclude network interface and conduit.
ENV OMPI_MCA_pml=^ucx            \
    OMPI_MCA_btl=tcp,self           \
    OMPI_MCA_btl_tcp_if_exclude=lo,docker0,veth_def_agent\
    OPAL_PREFIX=/opt/amazon/openmpi \
    NCCL_SOCKET_IFNAME=^docker,lo,veth

## Turn off PMIx Error https://github.com/open-mpi/ompi/issues/7516
ENV PMIX_MCA_gds=hash

## Set LD_PRELOAD for NCCL library
ENV LD_PRELOAD /opt/nccl/build/lib/libnccl.so


###################################################
## Install NVSHMEM with your specific flags
ARG NVSHMEM_VERSION=3.2.5-1


# Set all your specific NVSHMEM build environment variables
ENV CUDA_HOME=/usr/local/cuda \
	NVSHMEM_IBGDA_SUPPORT=1 \
	NVSHMEM_TIMEOUT_DEVICE_POLLING=0 \
	NVSHMEM_USE_GDRCOPY=1 \
	NVSHMEM_IBRC_SUPPORT=1 \
	NVSHMEM_BUILD_EXAMPLES=0 \
	NVSHMEM_MPI_SUPPORT=1 \
	NVSHMEM_PMIX_SUPPORT=1 \
	NVSHMEM_LIBFABRIC_SUPPORT=1 \
	LIBFABRIC_HOME=/opt/amazon/efa \
	MPI_HOME=/opt/amazon/openmpi\
	PMIX_HOME=/opt/amazon/pmix \
	CMAKE_CUDA_ARCHITECTURES=90a \
    NVSHMEM_DIR=/opt/nvshmem \
    NVSHMEM_HOME=/opt/nvshmem \
    GDRCOPY_HOME=/opt/gdrcopy \
    NCCL_HOME=/opt/nccl/build \
    NCCL_INCLUDE=/opt/nccl/build/include \
	NVSHMEM_SHMEM_SUPPORT=0 \
	NVSHMEM_UCX_SUPPORT=0 \
	NVSHMEM_USE_NCCL=0 \
	NVSHMEM_BUILD_TESTS=0 \
	NVSHMEM_BUILD_HYDRA_LAUNCHER=0 \
	NVSHMEM_BUILD_TXZ_PACKAGE=0

#[KeitaW](https://github.com/KeitaW)[deepep-dose-not-work-over-efa]

	#NVSHMEM_USE_NCCL=1
	#NVSHMEM_BUILD_TESTS=1
	#NVSHMEM_BUILD_HYDRA_LAUNCHER=1
	#NVSHMEM_BUILD_TXZ_PACKAGE=1
	#NVSHMEM_DEBUG=WARN
	#NVSHMEM_TRACE=1

    
WORKDIR /opt
RUN echo "=== Downloading and Building NVSHMEM ${NVSHMEM_VERSION} ===" && \
    echo "Using fixed download method with proper paths..." && \
    mkdir -p /tmp/nvshmem-build && \
    cd /tmp/nvshmem-build && \
    echo "Downloading NVSHMEM source..." && \
    curl -L "https://developer.nvidia.com/downloads/assets/secure/nvshmem/nvshmem_src_${NVSHMEM_VERSION}.txz" -o "nvshmem_src_${NVSHMEM_VERSION}.txz" && \
    echo "Verifying download..." && \
    ls -la "nvshmem_src_${NVSHMEM_VERSION}.txz" && \
    file "nvshmem_src_${NVSHMEM_VERSION}.txz" && \
    echo "Extracting archive..." && \
    tar -xf "nvshmem_src_${NVSHMEM_VERSION}.txz" && \
    cd nvshmem_src && \
    echo "NVSHMEM source extracted successfully" && \
    ls -la && \
    echo "Building with Ninja using your exact command pattern..." && \
	cmake -G Ninja -S . -B build -DCMAKE_INSTALL_PREFIX=/opt/nvshmem \
	    -DCUDA_HOME=${CUDA_HOME} \
	    -DCMAKE_CUDA_ARCHITECTURES=${CMAKE_CUDA_ARCHITECTURES} \
	    -DNVSHMEM_IBGDA_SUPPORT=${NVSHMEM_IBGDA_SUPPORT} \
	    -DNVSHMEM_SHMEM_SUPPORT=${NVSHMEM_SHMEM_SUPPORT} \
	    -DNVSHMEM_UCX_SUPPORT=${NVSHMEM_UCX_SUPPORT} \
	    -DNVSHMEM_USE_NCCL=${NVSHMEM_USE_NCCL} \
	    -DNVSHMEM_PMIX_SUPPORT=${NVSHMEM_PMIX_SUPPORT} \
	    -DNVSHMEM_TIMEOUT_DEVICE_POLLING=${NVSHMEM_TIMEOUT_DEVICE_POLLING} \
	    -DNVSHMEM_USE_GDRCOPY=${NVSHMEM_USE_GDRCOPY} \
	    -DNVSHMEM_IBRC_SUPPORT=${NVSHMEM_IBRC_SUPPORT} \
	    -DNVSHMEM_BUILD_TESTS=${NVSHMEM_BUILD_TESTS} \
	    -DNVSHMEM_BUILD_EXAMPLES=${NVSHMEM_BUILD_EXAMPLES} \
	    -DNVSHMEM_MPI_SUPPORT=${NVSHMEM_MPI_SUPPORT} \
	    -DNVSHMEM_BUILD_HYDRA_LAUNCHER=${NVSHMEM_BUILD_HYDRA_LAUNCHER} \
	    -DNVSHMEM_BUILD_TXZ_PACKAGE=${NVSHMEM_BUILD_TXZ_PACKAGE} \
	    -DNVSHMEM_LIBFABRIC_SUPPORT=${NVSHMEM_LIBFABRIC_SUPPORT} \
	    -DMPI_HOME=${MPI_HOME} \
	    -DPMIX_HOME=${PMIX_HOME} \
	    -DGDRCOPY_HOME=${GDRCOPY_HOME} \
	    -DLIBFABRIC_HOME=${LIBFABRIC_HOME} \
	    -DNCCL_HOME=${NCCL_HOME} \
	    -DNCCL_INCLUDE=${NCCL_INCLUDE} && \
    cmake --build build/ --target install && \
    echo "NVSHMEM installation completed successfully" && \
    cd / && rm -rf /tmp/nvshmem-build


ENV PATH=/opt/nvshmem/bin:$PATH LD_LIBRARY_PATH=/opt/amazon/pmix/lib:/opt/nvshmem/lib:$LD_LIBRARY_PATH NVSHMEM_REMOTE_TRANSPORT=libfabric NVSHMEM_LIBFABRIC_PROVIDER=efa


###################################################
## DeepEP
WORKDIR /workspace
RUN git clone https://github.com/dmvevents/DeepEP.git && cd DeepEP \
    && ./install.sh

###################################################
## Final Environment Setup
WORKDIR /workspace/DeepEP

RUN echo "/opt/nccl/build/lib" > /etc/ld.so.conf.d/nccl.conf && ldconfig
ENV LD_LIBRARY_PATH=/opt/nccl/build/lib:$LD_LIBRARY_PATH

# Also ensure other libraries are registered (optional but good practice)
RUN echo "/opt/amazon/openmpi/lib" > /etc/ld.so.conf.d/ompi.conf && \
    echo "/opt/amazon/efa/lib" > /etc/ld.so.conf.d/efa.conf && \
    echo "/opt/nvshmem/lib" > /etc/ld.so.conf.d/nvshmem.conf && \
    ldconfig
