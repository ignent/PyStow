[English](README.md) | [中文](README_zh.md)

# DotKeeper

A lightweight, Python-based Dotfiles configuration management tool designed to help users conveniently manage, backup, and deploy configuration files on Linux/Unix systems. It provides both a command-line interface (CLI) and a web-based graphical user interface (GUI).

## Features

* **Interface**: Provides an efficient CLI and an intuitive Web GUI (Vue.js).
* **Deployment**: Supports a "Backup and Overwrite" strategy, automatically backing up conflicting files to `~/.dotfiles_backup` to prevent data loss.
* **Undo**: Supports "Undo" operations. When removing symlinks, it automatically restores backups if they exist; if no backup exists, it copies the original file from the repository back to the target location, ensuring system file integrity.
* **No Dependencies**: The core logic relies only on the Python standard library, requiring no pip packages to run.

## Installation and Usage

### Prerequisites

1. **System Environment**:
    * Python 3.8 or higher.
    * Linux / macOS environment (Windows is limited to WSL or partial support).

2. **Prepare Dotfiles Directory (Critical Step)**:
    Before using this tool, users **must** organize their configuration files into a unified directory (default is `~/.dotfiles`).

    **Directory Structure Standard**:
    First-level subdirectories under the root directory are treated as "Packages". The file structure within a package should match the target structure under the user's home directory (`~`).

    **Structure Example**:

    ```text
    /home/user/.dotfiles/      <-- Dotfiles Repository Root
    ├── nvim/                  <-- Package Name: nvim
    │   └── .config/
    │       └── nvim/
    │           └── init.vim   <-- Linked to: ~/.config/nvim/init.vim after deployment
    ├── zsh/                   <-- Package Name: zsh
    │   └── .zshrc             <-- Linked to: ~/.zshrc after deployment
    └── git/                   <-- Package Name: git
        └── .gitconfig         <-- Linked to: ~/.gitconfig after deployment
    ```

### How to Run

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/ignent/DotKeeper.git && cd DotKeeper
    ```

2. **Start Web Interface** (Default port 9012):

    ```bash
    python dotkeeper.py web
    ```

    The browser will automatically open `http://localhost:9012` after running.

3. **Use Command Line (CLI)**:
    * Scan package status:

        ```bash
        python dotkeeper.py scan
        ```

    * Deploy a package (e.g., `zsh`):

        ```bash
        python dotkeeper.py deploy zsh
        ```

    * Restore a package (e.g., `zsh`):

        ```bash
        python dotkeeper.py restore zsh
        ```

    * View help:

        ```bash
        python dotkeeper.py --help
        ```

## Configuration

* **Default Dotfiles Path**: `~/.dotfiles` (Can be modified via `--dotfiles` argument).
* **Default Target Path**: User home directory `~` (Can be modified via `--target` argument).
* **Backup Path**: `~/.dotfiles_backup` (Structure mirrors the dotfiles repository).
