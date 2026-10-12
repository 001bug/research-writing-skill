---
name: environment-setup
description: Use when Python environment setup is needed for data visualization or conda installation is required
---

## DSH 运行约定

仅在 DeepSeek Harness 中适用：先根据 `skill` 工具返回的 `resourceBase.path`
解析真实技能目录，再读取资源根目录的 `.dsh/RUNTIME.md`，按其中约定执行。
不要猜测仓库位置，也不要假定当前目录就是技能仓库。

```bash
> DSH / Linux：环境安装仅使用文末“DSH / Linux 独立环境”和 `.dsh/INSTALL.md`。
> 下面 Conda、全局 pip、镜像和 shell 初始化说明面向其他宿主，不在 DSH 适配流程中执行。

# 将占位符替换为本次 skill 工具返回的 resourceBase.path（保留引号）。
SKILL_DIR="$(realpath '<resourceBase.path>')"
RESEARCH_WRITING_ROOT="$(dirname "$(dirname "$SKILL_DIR")")"
RESEARCH_WRITING_PYTHON="${DSH_HOME:-$HOME/.dsh}/research-writing/.venv/bin/python"
PAPER_ROOT="$(pwd -P)"
cat "$RESEARCH_WRITING_ROOT/.dsh/RUNTIME.md"
```

脚本与内置模板使用资源根目录的绝对路径；论文、用户模板和计划写入当前论文工作区。
以上变量只在当前 shell 调用有效，后续调用应重新设置或使用已经解析的绝对路径。

# 环境配置

本技能用于在终端完成 Python 画图环境的全流程配置。

## 适用场景

- 用户要求安装 Miniconda
- 用户要求创建虚拟环境
- 用户要求"用 Python 画图"但环境未就绪
- 绘图脚本运行报环境相关错误

## Checklist

- [ ] 系统识别（macOS/Linux/Windows）
- [ ] Miniconda 安装/修复
- [ ] conda 初始化
- [ ] 创建 `research` 环境
- [ ] 安装绘图依赖
- [ ] 环境自检
- [ ] 更新 `plan/progress.md`

## 一、系统识别

### macOS / Linux

```bash
uname -s
uname -m
echo "$SHELL"
```

### Windows PowerShell

```powershell
$PSVersionTable.PSVersion
$env:OS
```

## 二、Miniconda 安装

### macOS 全自动流程

```bash
set -euo pipefail

# 1) 选择安装包
ARCH="$(uname -m)"
if [ "$ARCH" = "arm64" ]; then
  URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
else
  URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
fi

# 2) 下载并静默安装
INSTALLER="$HOME/Downloads/miniconda.sh"
curl -fsSL "$URL" -o "$INSTALLER"
bash "$INSTALLER" -b -p "$HOME/miniconda3"

# 3) 当前 shell 立即可用
export PATH="$HOME/miniconda3/bin:$PATH"

# 4) 初始化 shell
"$HOME/miniconda3/bin/conda" init "$(basename "$SHELL")"

# 5) 验证
conda --version
```

### Windows 全自动流程（PowerShell）

```powershell
$ErrorActionPreference = "Stop"

# 1) 下载
$installer = Join-Path $env:TEMP "Miniconda3-latest-Windows-x86_64.exe"
Invoke-WebRequest -Uri "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe" -OutFile $installer

# 2) 静默安装
$target = "$env:USERPROFILE\miniconda3"
Start-Process -FilePath $installer -ArgumentList "/InstallationType=JustMe","/RegisterPython=0","/S","/D=$target" -Wait

# 3) 初始化 powershell
& "$target\Scripts\conda.exe" init powershell

# 4) 验证
$env:Path = "$target;$target\Scripts;$target\condabin;" + $env:Path
conda --version
```

## 三、创建科研虚拟环境

**默认环境名**：`research`

### 创建与激活

```bash
conda create -n research python=3.11 -y
conda activate research
python -m pip install --upgrade pip
```

## 四、安装绘图依赖

```bash
pip install numpy pandas scipy matplotlib seaborn scikit-learn statsmodels jupyter ipykernel openpyxl
python -m ipykernel install --user --name research --display-name "Python (research)"
```

可选：

```bash
pip install plotly pingouin
```

## 五、环境自检

```bash
python - <<'PY'
import sys
import numpy, pandas, matplotlib, seaborn, sklearn, statsmodels
print('Python:', sys.version.split()[0])
print('numpy:', numpy.__version__)
print('pandas:', pandas.__version__)
print('matplotlib:', matplotlib.__version__)
print('seaborn:', seaborn.__version__)
print('sklearn:', sklearn.__version__)
print('statsmodels:', statsmodels.__version__)
print('ENV CHECK: OK')
PY
```

## 六、画图任务前检查

执行画图任务前，至少确认：
1. 已激活 `research` 环境
2. `matplotlib` 和 `seaborn` 导入正常
3. 输出目录存在（如 `figures/`）

## 七、常见问题与修复

### `conda: command not found`

macOS / Linux：
```bash
export PATH="$HOME/miniconda3/bin:$PATH"
conda init "$(basename "$SHELL")"
```

Windows PowerShell：
```powershell
$env:Path = "$env:USERPROFILE\miniconda3;$env:USERPROFILE\miniconda3\Scripts;" + $env:Path
```

### 下载慢或超时

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 包冲突

```bash
conda create -n research_clean python=3.11 -y
conda activate research_clean
pip install -r requirements.txt
```

## 八、执行约束

<HARD-GATE>
1. 用户提到"安装环境/画图报错"，优先执行本技能
2. 先识别系统，再给对应命令，禁止跨系统混发命令
3. 执行完成后，必须回写 `plan/progress.md`
</HARD-GATE>


## DSH / Linux 独立环境

使用 `.dsh/INSTALL.md` 中的虚拟环境安装步骤，运行
`"$RESEARCH_WRITING_PYTHON" -m pip ...`，不要改动系统 Python、全局镜像或其他项目环境。
优先用 `requirements-dsh.lock.txt` 复现本机已验证版本。
不依赖 Conda，不要求重启电脑。缺少可选 TeX 编译器时报告限制，仍可输出 LaTeX 源码。
