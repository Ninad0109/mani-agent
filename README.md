
# ManiAgent: A Multi-Agent Framework for General-Purpose Manipulation Tasks

## 项目简介
ManiAgent是一个将通用操作任务拆解成多个agent相互配合完成任务的框架，此仓库实现的是在SimplerEnv仿真环境中进行ManiAgent算法部署，完成对应任务的功能。因此，我们开源了controller、object detector以及grasper的对应代码和prompt，reasoner以及更多部分的代码正在整理中，预计很快开源。

[![arXiv](https://img.shields.io/badge/arXiv-Paper-red?style=for-the-badge&logo=arxiv&logoColor=white)](https://arxiv.org/abs/xxxx.xxxxx)
[![Project Page](https://img.shields.io/badge/Project-Page-blue?style=for-the-badge&logo=googlechrome&logoColor=white)](https://yi-yang929.github.io/ManiAgent/)


## 运行指南（conda环境）

本项目使用flask打包多个不同的app，实现不同的功能，要实现功能，我们一共需要配置三个环境。
我们建议使用11.8版本的cuda，以避免兼容性问题。

首先，下载代码。
```
git clone https://github.com/yi-yang929/maniagent.git
cd maniagent
git submodule update --init --recursive
```

### 1. agent环境

首先创建环境
```
conda create -n agent python=3.10 -y
conda activate agent
```
安装torch
```
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

# If you are in China
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 -f https://mirrors.aliyun.com/pytorch-wheels/cu118/
```
安装其他包
```
pip install -r requirements.txt
```

### 2. anygrasp环境

请按照[`官方教程`](grasper/anygrasp_ManiAgent/README.md)进行配置。

### 3. SimplerEnv环境

请按照[`官方教程`](benchmark/simpler/README.md)进行配置。

## 运行

如果各agent不在同设备上运行，则需要额外修改各app中的host参数，并进行端口映射，以形成有效通信。

controller启动：
```
python controller/app.py
```

object detector启动：
```
python object_detector/app.py
```

grasper启动：
```
cd grasper/anygrasp_ManiAgent/grasp_detection
python app.py

```

启动仿真器
```
cd benchmark
bash scripts/env_sh/simpler.sh ./evaluation/configs/simpler/example_simpler_yy.yaml
```

## 联系我们

如有问题，请通过邮箱联系：yangyi_00929@163.com