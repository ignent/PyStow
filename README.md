# Dotfiles 管理工具 (Dotfiles Management Tool)

这是一个基于 Python 的轻量级 Dotfiles 配置管理工具，旨在帮助用户方便地管理、备份和部署 Linux/Unix 系统下的配置文件。它提供了命令行界面 (CLI) 和 Web 图形界面 (GUI)。

## 功能特性

* **界面**: 提供高效的 CLI 和直观的 Web GUI (Vue.js)。
* **部署**: 支持“备份并覆盖”策略，自动将冲突文件备份到 `~/.dotfiles_backup`，防止数据丢失。
* **撤销**: 支持“撤销 (Undo)”操作。移除软链接时，如果存在备份会自动恢复；如果没有备份，则自动将仓库中的原文件复制回目标位置，确保系统文件完整。
* **无依赖**: 核心逻辑仅依赖 Python 标准库，无需安装 pip 包即可运行。

## 安装与运行

### 前置要求

1. **系统环境**:
    * Python 3.8 或更高版本。
    * Linux / macOS 环境 (Windows 下仅限 WSL 或部分支持)。

2. **准备 Dotfiles 目录 (关键步骤)**:
    在使用本工具前，用户**必须**将配置文件整理到一个统一的目录中（默认为 `~/.dotfiles`）。

    **目录结构规范**:
    根目录下的一级子目录被视为“包 (Package)”。包内的文件结构应与用户主目录 (`~`) 下的目标结构保持一致。

    **结构示例**:

    ```text
    /home/user/.dotfiles/      <-- Dotfiles 仓库根目录
    ├── nvim/                  <-- 包名: nvim
    │   └── .config/
    │       └── nvim/
    │           └── init.vim   <-- 部署后链接至: ~/.config/nvim/init.vim
    ├── zsh/                   <-- 包名: zsh
    │   └── .zshrc             <-- 部署后链接至: ~/.zshrc
    └── git/                   <-- 包名: git
        └── .gitconfig         <-- 部署后链接至: ~/.gitconfig
    ```

### 运行方式

1. **克隆仓库**:

    ```bash
    git clone https://github.com/ignent/PyStow.git && cd PyStow
    ```

2. **启动 Web 界面** (默认端口 9012):

    ```bash
    python3 src/main.py web
    ```

    运行后浏览器会自动打开 `http://localhost:9012`。

3. **使用命令行 (CLI)**:
    * 扫描包状态:

        ```bash
        python3 src/main.py scan
        ```

    * 部署包 (例如 `nvim`):

        ```bash
        python3 src/main.py deploy nvim
        ```

    * 撤销包 (例如 `nvim`):

        ```bash
        python3 src/main.py restore nvim
        ```

    * 查看帮助:

        ```bash
        python3 src/main.py --help
        ```

## 配置说明

* **默认 Dotfiles 路径**: `~/.dotfiles` (可通过 `--dotfiles` 参数修改)。
* **默认目标路径**: 用户主目录 `~` (可通过 `--target` 参数修改)。
* **备份路径**: `~/.dotfiles_backup` (结构与 dotfiles 仓库一致)。
