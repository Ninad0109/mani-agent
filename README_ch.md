
# ManiAgent: A Multi-Agent Framework for General-Purpose Manipulation Tasks

## 项目简介
ManiAgent是一个将通用操作任务拆解成多个agent相互配合完成任务的框架，此仓库实现的是在SimplerEnv仿真环境中进行ManiAgent算法部署，完成对应任务的功能。因此，我们开源了controller、object detector以及grasper的对应代码和prompt，reasoner以及更多部分的代码正在整理中，预计很快开源。

[![arXiv](https://img.shields.io/badge/arXiv-Paper-red?style=plastic&logo=arxiv&logoColor=white)](https://arxiv.org/abs/2510.11660)
[![Project Page](https://img.shields.io/badge/Project-Page-blue?style=plastic&logo=googlechrome&logoColor=white)](https://yi-yang929.github.io/ManiAgent/)
[![English README](https://img.shields.io/badge/English-README-yellow?style=plastic&logo=googledocs&logoColor=white)](./README.md)


<p align="center">
  <img src="./assets/method_overall_01.png" alt="Framework">
  <br>
  <em>图 1: 这是我们的整体框架图。</em>
</p>

## 目录
- [项目简介](#项目简介)
- [目录](#目录)
- [推荐配置](#推荐配置)
- [运行指南（conda环境）](#运行指南conda环境)
  - [1. agent环境](#1-agent环境)
  - [2. anygrasp环境](#2-anygrasp环境)
  - [3. SimplerEnv环境](#3-simplerenv环境)
    - [错误排查](#错误排查)
  - [4. 运行](#4-运行)
- [运行指南（docker）](#运行指南docker)
- [自定义任务](#自定义任务)
  - [无需配置Anygrasp环境的最小实现](#无需配置anygrasp环境的最小实现)
  - [详细参数说明](#详细参数说明)
    - [1. controller](#1-controller)
    - [2. object detector](#2-object-detector)
    - [3. prompt manager](#3-prompt-manager)
    - [4. grasper](#4-grasper)
    - [5. simpler](#5-simpler)
- [联系我们](#联系我们)




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

# Using Ali mirror
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 -f https://mirrors.aliyun.com/pytorch-wheels/cu118/
```
安装其他包
```bash
pip install -r requirements.txt
```

### 2. anygrasp环境

请按照[`官方教程`](https://github.com/yi-yang929/anygrasp_ManiAgent.git)进行配置。

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

### 4. 运行

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
我们将agent环境和simpler_env仿真环境打包到了docker中，但是由于Anygrasp的限制，我们没有将Anygrasp打包到docker中，因此需要额外配置Anygrasp环境。请参考[官方教程](https://github.com/yi-yang929/anygrasp_ManiAgent.git)进行配置，并使用我们的[anygrasp](https://github.com/yi-yang929/anygrasp_ManiAgent.git)代码运行。
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

## 自定义任务

### 无需配置Anygrasp环境的最小实现
如果你认为Anygrasp的配置较为复杂，可以使用我们的最小实现代码，由于SimplerEnv中的叠方块任务实际上无需使用Anygrasp，因此你可以在[simpler.sh](benchmark/scripts/env_sh/simpler.sh)中修改任务，例如改成下面的样式：
```bash
conda init && source activate
conda activate simpler_env

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the project root directory (two levels up from scripts/env_sh/)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Set default configuration file path
config_path="$PROJECT_ROOT/evaluation/configs/simpler/example_simpler.yaml"

# Check if configuration file parameter is passed
if [[ $# -gt 0 ]]; then
    config_path="$1"
fi

# Verify if configuration file exists
if [[ ! -f "$config_path" ]]; then
    echo "[ERROR] Configuration file does not exist: $config_path"
    exit 1
fi

echo "[INFO] Using configuration file: $config_path"

# Execute evaluation
for init_rng in 0 2 4; do
    python $PROJECT_ROOT/evaluation/run_simpler_evaluation.py --config ${config_path} \
    --set octo-init-rng ${init_rng} --set additional-env-save-tags octo_init_rng_${init_rng} \
    --set env-name StackGreenCubeOnYellowCubeBakedTexInScene-v0 --set scene-name bridge_table_1_v1 \
    --set rgb-overlay-path simpler/ManiSkill2_real2sim/data/real_inpainting/bridge_real_eval_1.png \
    --set robot widowx --set robot-init-x-range "0.147,0.147,1" --set robot-init-y-range "0.028,0.028,1";
done
```
然后直接运行
```bash
cd benchmark
bash scripts/env_sh/simpler.sh ./evaluation/configs/simpler/example_simpler.yaml
```
即可在不配置Anygrasp的情况下尝试我们的代码。（由于减少了抓取位姿偏移带来的影响，通过此种方式运行的仿真效果往往高于使用Anygrasp的表现，但是实际上这是牺牲了通用型带来的特定任务上的性能提升，因此建议此方法仅作为环境测试使用。）

### 详细参数说明
下面介绍我们代码中可以较为方便定义的参数，在运行代码的时候，可以通过 `--param [value]` 的方式来修改参数。
#### 1. controller
| 参数 | 说明与示例 |
| :------- | :---------- |
| `--model` | 指定输出动作所用的LLM模型<br>**示例**: `--model gpt-5 ` |
| `--model_detect` | 指定得到检测物品信息的LLM模型（建议选择较为轻量的模型以加快运行速度）<br>**示例**: `--model_detect gpt-5 ` |
| `--port` | 指定服务所部署的端口<br>**示例**: `--port 9500 ` |
| `--host` | 指定服务所部署的ip<br>**示例**: `--host 127.0.0.1 ` |
| `--use-cache` | (布尔值)决定是否使用参数化动作序列缓存<br>**示例**: `--use-cache ` |

#### 2. object detector
| 参数 | 说明与示例 |
| :------- | :---------- |
| `--detect-model` | 指定所用的检测模型<br>**示例**: `--detect-model microsoft/Florence-2-large ` |
| `--vlm-model` | 指定当出现多个检测物体，进行物体筛选所用的VLM（注意选取具有图片理解功能的VLM）<br>**示例**: `--vlm-model gpt-5` |
| `--port` | 指定服务所部署的端口<br>**示例**: `--port 4399 ` |
| `--host` | 指定服务所部署的ip<br>**示例**: `--host 127.0.0.1 ` |

#### 3. prompt manager
| 参数 | 说明与示例 |
| :------- | :---------- |
| `--port` | 指定服务所部署的端口<br>**示例**: `--port 4599 ` |
| `--host` | 指定服务所部署的ip<br>**示例**: `--host 127.0.0.1 ` |

#### 4. grasper
| 参数 | 说明与示例 |
| :------- | :---------- |
| `--port` | 指定服务所部署的端口<br>**示例**: `--port 4499 ` |
| `--host` | 指定服务所部署的ip<br>**示例**: `--host 127.0.0.1 ` |

#### 5. simpler
参数可以通过对[simpler.sh](benchmark/scripts/env_sh/simpler.sh)和[example_simpler.yaml](benchmark/evaluation/configs/simpler/example_simpler.yaml)进行修改来定义。具体可参考[上面章节](#无需配置Anygrasp环境的最小实现)的描述，此处不再赘述。


## 联系我们

如有问题，请通过邮箱联系：[yangyi_00929@163.com](mailto:yangyi_00929@163.com)。