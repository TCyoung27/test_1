# 部署

以下步骤面向 Ubuntu 环境，建议先安装 VS Code 和 Miniconda，再通过 `environment.yml` 创建 Conda 主环境，并用 `requirements.txt` 补齐 pip 依赖。

## 1. 安装 VS Code

在 Ubuntu 上安装 VS Code，先下载 deb 包（`https://code.visualstudio.com/docs/setup/linux`）：

```bash
sudo dpkg -i vscode.deb
```

安装完成后，打开 VS Code，在 Extensions 中安装插件：

- Python：`ms-python.python`
- Pylance：`ms-python.vscode-pylance`
- YAML：`redhat.vscode-yaml`


## 2. 安装 Miniconda

普通 x86_64 Ubuntu 可以使用 Miniconda 管理 Python 环境：

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc
conda --version
```

如果安装后终端没有识别 `conda`，可以执行：

```bash
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

建议关闭 base 环境自动激活：

```bash
conda config --set auto_activate_base false
```

## 3. 创建项目环境

进入项目目录后，先用 `environment.yml` 创建 Conda 环境，再用 `requirements.txt` 安装 pip 依赖：


```bash
cd /path/to/2_CropAIRobot_vsc
conda env create -f environment.yml
conda activate Agent
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
#网速慢，用清华源
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

如果环境已经存在，可以按需要更新：

```bash
conda activate Agent
python -m pip install -r requirements.txt
```
