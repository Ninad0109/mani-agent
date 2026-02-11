FROM nvidia/cuda:11.8.0-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# Install dependencies
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && apt-get update -y && \
    apt-get install --assume-yes --fix-missing build-essential && \
    apt-get install -y curl  && \
    apt-get install -y apt-utils \
    tzdata \
    git wget curl vim unzip ffmpeg \
    build-essential cmake pkg-config \
    llvm meson \
    libegl1-mesa \
    libegl1-mesa-dev \
    libegl1 \
    libgl1 \
    mesa-utils \
    libsm6 libxext6 libxrender-dev \
    libosmesa6-dev \
    python3.10 \
    python3-pip \
    tmux
RUN sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list && apt-get update && apt-get build-dep -y mesa && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

# Install Conda
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-py310_25.7.0-2-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh

RUN /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

ENV PATH=/opt/conda/bin:$PATH

# Install Vulkan libraries
RUN apt-get update && apt-get install -y libvulkan1 mesa-vulkan-drivers vulkan-tools libglvnd-dev
RUN mkdir -p /usr/share/vulkan/icd.d \
             /usr/share/glvnd/egl_vendor.d \
             /etc/vulkan/implicit_layer.d && \
    printf '%s\n' \
    '{' \
    '    "file_format_version" : "1.0.0",' \
    '    "ICD": {' \
    '        "library_path": "libGLX_nvidia.so.0",' \
    '        "api_version" : "1.2.155"' \
    '    }' \
    '}' > /usr/share/vulkan/icd.d/nvidia_icd.json && \
    printf '%s\n' \
    '{' \
    '    "file_format_version" : "1.0.0",' \
    '    "ICD" : {' \
    '        "library_path" : "libEGL_nvidia.so.0"' \
    '    }' \
    '}' > /usr/share/glvnd/egl_vendor.d/10_nvidia.json && \
    printf '%s\n' \
    '{' \
    '    "file_format_version" : "1.0.0",' \
    '    "layer": {' \
    '        "name": "VK_LAYER_NV_optimus",' \
    '        "type": "INSTANCE",' \
    '        "library_path": "libGLX_nvidia.so.0",' \
    '        "api_version" : "1.2.155",' \
    '        "implementation_version" : "1",' \
    '        "description" : "NVIDIA Optimus layer",' \
    '        "functions": {' \
    '            "vkGetInstanceProcAddr": "vk_optimusGetInstanceProcAddr",' \
    '            "vkGetDeviceProcAddr": "vk_optimusGetDeviceProcAddr"' \
    '        },' \
    '        "enable_environment": {' \
    '            "__NV_PRIME_RENDER_OFFLOAD": "1"' \
    '        },' \
    '        "disable_environment": {' \
    '            "DISABLE_LAYER_NV_OPTIMUS_1": ""' \
    '        }' \
    '    }' \
    '}' > /etc/vulkan/implicit_layer.d/nvidia_layers.json

# Set up application directory
WORKDIR /app
COPY . /app

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install simpler environment
RUN /opt/conda/bin/conda create -n simpler_env python=3.10 -y && \
    /bin/bash -c "source activate simpler_env && \
        cd benchmark/simpler && \
        cd ManiSkill2_real2sim && pip install -e . && \
        cd .. && pip install -e . && \
        pip install matplotlib mediapy omegaconf hydra-core && pip install numpy==1.24.4 && \
        cd .."

# Install agent environment
RUN /opt/conda/bin/conda create -n agent python=3.10 -y && \
    /bin/bash -c "source activate agent && \
        pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118 && \
        pip install -r requirements.txt"

# environment
ENV OPENAI_API_KEY=your_api_key
ENV BASE_URL=https://api.openai.com/v1
ENV HF_ENDPOINT=https://huggingface.co
