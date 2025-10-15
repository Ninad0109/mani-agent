
# ManiAgent: A Multi-Agent Framework for General-Purpose Manipulation Tasks

## 项目简介
ManiAgent是一个将通用操作任务拆解成多个agent相互配合完成任务的框架，此仓库实现的是在SimplerEnv仿真环境中进行ManiAgent算法部署，完成对应任务的功能。因此，我们开源了controller、object detector以及grasper的对应代码和prompt，reasoner以及更多部分的代码正在整理中，预计很快开源。

[![arXiv](https://img.shields.io/badge/arXiv-Paper-red?style=plastic&logo=arxiv&logoColor=white)](https://arxiv.org/abs/2510.11660)
[![Project Page](https://img.shields.io/badge/Project-Page-blue?style=plastic&logo=googlechrome&logoColor=white)](https://yi-yang929.github.io/ManiAgent/)

## 推荐配置
GPU：16g或以上VRAM的Nvidia显卡

## 运行指南（conda环境）

本项目使用flask打包多个不同的app，实现不同的功能，要实现功能，我们一共需要配置三个环境。
我们建议使用11.8版本的cuda，以避免兼容性问题。

首先，下载代码。
```bash
git clone https://github.com/yi-yang929/maniagent.git
cd maniagent
git submodule update --init --recursive
```

### 1. agent环境

首先创建环境
```bash
conda create -n agent python=3.10 -y
conda activate agent
```
配置LLM api和base_url(如果有的话)
```bashrc
echo 'export OPENAI_API_KEY=your_api_key' >> ~/.bashrc
echo 'export BASE_URL=https://api.openai.com/v1' >> ~/.bashrc
source ~/.bashrc
```
安装torch
```bash
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# If you are in China
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 -f https://mirrors.aliyun.com/pytorch-wheels/cu118/
```
安装其他包
```bash
pip install -r requirements.txt
```

### 2. anygrasp环境

请按照[`官方教程`](grasper/anygrasp_ManiAgent/README.md)进行配置。

### 3. SimplerEnv环境

首先创建环境
```bash
conda create -n simpler_env python=3.10
conda activate simpler_env
```
安装ffmpeg
```bash
sudo apt-get install ffmpeg
```
安装SimplerEnv和ManiSkill
```bash
cd ./benchmark/simpler/ManiSkill2_real2sim
pip install -e .
cd ..
pip install -e .
pip install matplotlib mediapy omegaconf hydra-core && pip install numpy==1.24.4
```
#### 错误排查
如果你的simplerenv运行时出现x11相关的依赖问题，可以运行以下代码：
```bash
su
# （输入密码）
apt-get update && apt-get install -y libvulkan1 mesa-vulkan-drivers vulkan-tools libglvnd-dev
mkdir -p /usr/share/vulkan/icd.d \
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
```

## 运行

如果各agent不在同设备上运行，则需要额外修改各app中的host参数，并进行端口映射，以形成有效通信。

controller启动：
```bash
python controller/app.py
```

object detector启动：
```bash
python object_detector/app.py
```

grasper启动：
```bash
cd grasper/anygrasp_ManiAgent/grasp_detection
python app.py

```

启动仿真器
```bash
cd benchmark
bash scripts/env_sh/simpler.sh ./evaluation/configs/simpler/example_simpler.yaml
```

## 运行指南（docker）
我们将agent环境和simpler_env仿真环境打包到了docker中，但是由于Anygrasp的限制，我们没有将Anygrasp打包到docker中，因此需要额外配置Anygrasp环境。请参考官方教程进行配置，并使用我们的[anygrasp](grasper/anygrasp_ManiAgent/)代码运行。
首先，下载代码。
```bash
git clone https://github.com/yi-yang929/maniagent.git
cd maniagent
git submodule update --init --recursive
```
其次，请打开[dockerfile](Dockerfile)并修改`ENV`中的`OPENAI_API_KEY`和`BASE_URL`为你的api key和base url。
同时，你也可以根据当地的网络情况选择合适的镜像源。
构建docker
```bash
docker build -t maniagent .
```
启动docker，注意端口的映射
```bash
docker run -it --gpus all \
-v $(pwd):/workspace \
-p 127.0.0.1:9500:9500 \
-p 127.0.0.1:4399:4399 \
-p 127.0.0.1:4599:4599 \
--add-host=host.docker.internal:host-gateway \
--network bridge \
maniagent:latest \
/bin/bash
```

进入agent环境
```bash
# （docker）
conda init && source activate
conda activate agent
```
运行controller
```bash
# （docker）
tmux new -s controller
python controller/app.py
# (ctrl+b，d退出tmux)
```
运行detector
```bash
# （docker）
tmux new -s detector
python detector/app.py
# (ctrl+b，d退出tmux)
```
运行prompt_manager
```bash
# （docker）
tmux new -s prompt_manager
python prompt_manager/app.py
# (ctrl+b，d退出tmux)
```
运行grasper

```bash
# (host)
cd grasper/anygrasp_ManiAgent/grasp_detection
python app.py
```
进入仿真器环境并运行仿真
```bash
# （docker）
tmux new -s simpler_env
cd benchmark
bash scripts/env_sh/simpler.sh ./evaluation/configs/simpler/example_simpler.yaml
# (ctrl+b，d退出tmux)
```




## 联系我们

如有问题，请通过邮箱联系：yangyi_00929@163.com