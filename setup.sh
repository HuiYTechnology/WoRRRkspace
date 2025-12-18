#!/usr/bin/env bash
set -euo pipefail

VERSION="1.0.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ══════════════════════════════════════════════════════════════════════════════
#                              LOCALIZATION
# ══════════════════════════════════════════════════════════════════════════════

LANG_CODE="en"
declare -A L

set_language_en() {
    L[select_lang]="Select language / Выберите язык:"
    L[detecting_distro]="Detecting Linux distribution..."
    L[detected]="Detected"
    L[detecting_gpus]="Detecting GPUs..."
    L[primary_gpu]="Primary GPU type"
    L[detecting_conda]="Detecting conda/mamba..."
    L[found]="Found"
    L[not_found]="Not found"
    L[nvidia_driver_not_loaded]="NVIDIA GPU found but driver not loaded"
    L[distribution]="Distribution"
    L[graphics]="Graphics"
    L[driver]="Driver"
    L[no_gpu]="No GPU detected"
    L[selected]="Selected"
    L[conda_mamba]="Conda/Mamba"
    L[system_info]="SYSTEM INFORMATION"
    L[what_to_do]="What would you like to do?"
    L[menu_1]="Quick setup (generate + create env)"
    L[menu_2]="Quick setup + install system packages"
    L[menu_3]="Full setup (packages + env + playwright)"
    L[menu_4]="Choose different GPU type"
    L[menu_5]="Only generate environment.yml"
    L[menu_6]="Only create conda env"
    L[menu_7]="Install micromamba"
    L[menu_0]="Exit"
    L[choice]="Choice"
    L[select_gpu]="Select GPU type:"
    L[generating]="Generating"
    L[generated]="Generated"
    L[installing_packages]="Installing system packages..."
    L[some_failed]="Some packages failed"
    L[packages_installed]="System packages installed"
    L[unknown_distro]="Unknown distro, skipping"
    L[installing_micromamba]="Installing micromamba..."
    L[micromamba_installed]="Micromamba installed to"
    L[restart_shell]="Restart shell: source ~/.bashrc"
    L[creating_env]="Creating environment"
    L[env_created]="Environment created!"
    L[activate_with]="Activate with:"
    L[failed_create]="Failed to create environment"
    L[no_conda]="No conda/mamba available"
    L[install_micromamba_q]="No conda found. Install micromamba?"
    L[installing_playwright]="Installing Playwright browsers..."
    L[env_not_found]="environment.yml not found"
    L[invalid_choice]="Invalid choice"
    L[press_enter]="Press Enter to continue..."
    L[goodbye]="Goodbye!"
    L[searching_aur]="Searching AUR/system conda..."
    L[will_use]="Will use"
}

set_language_ru() {
    L[select_lang]="Select language / Выберите язык:"
    L[detecting_distro]="Определение дистрибутива Linux..."
    L[detected]="Обнаружено"
    L[detecting_gpus]="Поиск GPU..."
    L[primary_gpu]="Основной тип GPU"
    L[detecting_conda]="Поиск conda/mamba..."
    L[found]="Найдено"
    L[not_found]="Не найдено"
    L[nvidia_driver_not_loaded]="NVIDIA GPU найден, но драйвер не загружен"
    L[distribution]="Дистрибутив"
    L[graphics]="Графика"
    L[driver]="Драйвер"
    L[no_gpu]="GPU не обнаружен"
    L[selected]="Выбрано"
    L[conda_mamba]="Conda/Mamba"
    L[system_info]="ИНФОРМАЦИЯ О СИСТЕМЕ"
    L[what_to_do]="Что вы хотите сделать?"
    L[menu_1]="Быстрая установка (генерация + создание env)"
    L[menu_2]="Быстрая установка + системные пакеты"
    L[menu_3]="Полная установка (пакеты + env + playwright)"
    L[menu_4]="Выбрать другой тип GPU"
    L[menu_5]="Только сгенерировать environment.yml"
    L[menu_6]="Только создать conda env"
    L[menu_7]="Установить micromamba"
    L[menu_0]="Выход"
    L[choice]="Выбор"
    L[select_gpu]="Выберите тип GPU:"
    L[generating]="Генерация"
    L[generated]="Сгенерировано"
    L[installing_packages]="Установка системных пакетов..."
    L[some_failed]="Некоторые пакеты не установились"
    L[packages_installed]="Системные пакеты установлены"
    L[unknown_distro]="Неизвестный дистрибутив, пропуск"
    L[installing_micromamba]="Установка micromamba..."
    L[micromamba_installed]="Micromamba установлен в"
    L[restart_shell]="Перезапустите shell: source ~/.bashrc"
    L[creating_env]="Создание окружения"
    L[env_created]="Окружение создано!"
    L[activate_with]="Активировать:"
    L[failed_create]="Не удалось создать окружение"
    L[no_conda]="conda/mamba не найден"
    L[install_micromamba_q]="Conda не найден. Установить micromamba?"
    L[installing_playwright]="Установка браузеров Playwright..."
    L[env_not_found]="environment.yml не найден"
    L[invalid_choice]="Неверный выбор"
    L[press_enter]="Нажмите Enter для продолжения..."
    L[goodbye]="До свидания!"
    L[searching_aur]="Поиск AUR/системной conda..."
    L[will_use]="Будет использован"
}

select_language() {
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo ""
    echo "  1) English"
    echo "  2) Русский"
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    read -p "  Select / Выберите [1]: " lang_choice
    
    case "${lang_choice:-1}" in
        2|ru|р)
            LANG_CODE="ru"
            set_language_ru
            ;;
        *)
            LANG_CODE="en"
            set_language_en
            ;;
    esac
    echo ""
}

# ══════════════════════════════════════════════════════════════════════════════
#                                 COLORS & ICONS
# ══════════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'

ICON_OK="✓"
ICON_FAIL="✗"
ICON_WARN="⚠"
ICON_INFO="ℹ"
ICON_GEAR="⚙"
ICON_PKG="📦"
ICON_GPU="🎮"
ICON_CPU="💻"

# ══════════════════════════════════════════════════════════════════════════════
#                             LOGGING FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

log_info()    { echo -e "${BLUE}${ICON_INFO}${NC} $1"; }
log_success() { echo -e "${GREEN}${ICON_OK}${NC} $1"; }
log_warn()    { echo -e "${YELLOW}${ICON_WARN}${NC} $1"; }
log_error()   { echo -e "${RED}${ICON_FAIL}${NC} $1"; }
log_step()    { echo -e "${PURPLE}${ICON_GEAR}${NC} $1"; }

# ══════════════════════════════════════════════════════════════════════════════
#                           DISTRO DETECTION
# ══════════════════════════════════════════════════════════════════════════════

declare -A DISTRO_INFO
declare -A PKG_COMMANDS

detect_distro() {
    log_step "${L[detecting_distro]}"
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO_INFO[id]="${ID:-unknown}"
        DISTRO_INFO[pretty]="${PRETTY_NAME:-Unknown Linux}"
    else
        DISTRO_INFO[id]="unknown"
        DISTRO_INFO[pretty]="Unknown Linux"
    fi
    
    case "${DISTRO_INFO[id]}" in
        ubuntu|debian|linuxmint|pop|elementary|zorin|kali|raspbian|neon)
            DISTRO_INFO[family]="debian"
            PKG_COMMANDS[manager]="apt"
            PKG_COMMANDS[update]="sudo apt update"
            PKG_COMMANDS[install]="sudo apt install -y"
            ;;
        arch|manjaro|endeavouros|garuda|artix|arcolinux|cachyos)
            DISTRO_INFO[family]="arch"
            PKG_COMMANDS[manager]="pacman"
            PKG_COMMANDS[update]="sudo pacman -Sy"
            PKG_COMMANDS[install]="sudo pacman -S --noconfirm --needed"
            ;;
        fedora|rhel|centos|rocky|almalinux)
            DISTRO_INFO[family]="rhel"
            PKG_COMMANDS[manager]="dnf"
            PKG_COMMANDS[update]="sudo dnf check-update || true"
            PKG_COMMANDS[install]="sudo dnf install -y"
            ;;
        opensuse*|sles|suse)
            DISTRO_INFO[family]="suse"
            PKG_COMMANDS[manager]="zypper"
            PKG_COMMANDS[update]="sudo zypper refresh"
            PKG_COMMANDS[install]="sudo zypper install -y"
            ;;
        *)
            DISTRO_INFO[family]="unknown"
            PKG_COMMANDS[manager]="unknown"
            ;;
    esac
    
    log_success "${L[detected]}: ${DISTRO_INFO[pretty]} (${DISTRO_INFO[family]})"
}

# ══════════════════════════════════════════════════════════════════════════════
#                              GPU DETECTION
# ══════════════════════════════════════════════════════════════════════════════

declare -A GPU_NVIDIA
declare -A GPU_AMD
declare -A GPU_INTEL
GPU_TYPE="cpu"

detect_nvidia() {
    GPU_NVIDIA[found]=false
    GPU_NVIDIA[name]=""
    GPU_NVIDIA[driver]=""
    GPU_NVIDIA[cuda]="12.1"
    
    if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
        GPU_NVIDIA[found]=true
        GPU_NVIDIA[name]=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 | xargs)
        GPU_NVIDIA[driver]=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 | xargs)
        
        local driver_major=$(echo "${GPU_NVIDIA[driver]}" | cut -d'.' -f1)
        if [[ "$driver_major" -ge 530 ]]; then
            GPU_NVIDIA[cuda]="12.1"
        else
            GPU_NVIDIA[cuda]="11.8"
        fi
        GPU_TYPE="nvidia"
    elif lspci 2>/dev/null | grep -iq 'nvidia'; then
        GPU_NVIDIA[found]=true
        GPU_NVIDIA[name]=$(lspci | grep -i 'vga\|3d' | grep -i 'nvidia' | head -1 | sed 's/.*: //')
        GPU_NVIDIA[driver]="not loaded"
    fi
}

detect_amd() {
    GPU_AMD[found]=false
    GPU_AMD[name]=""
    GPU_AMD[rocm]=""
    
    if lspci 2>/dev/null | grep -i 'vga\|3d\|display' | grep -iqE 'amd|radeon|advanced micro'; then
        GPU_AMD[found]=true
        GPU_AMD[name]=$(lspci | grep -i 'vga\|3d\|display' | grep -iE 'amd|radeon' | head -1 | sed 's/.*: //')
        
        if command -v rocm-smi &>/dev/null; then
            GPU_AMD[rocm]="installed"
        fi
        
        if [[ "${GPU_NVIDIA[found]}" == false ]]; then
            GPU_TYPE="amd"
        fi
    fi
}

detect_intel() {
    GPU_INTEL[found]=false
    GPU_INTEL[name]=""
    GPU_INTEL[is_arc]=false
    
    if lspci 2>/dev/null | grep -i 'vga\|3d\|display' | grep -iq 'intel'; then
        GPU_INTEL[found]=true
        GPU_INTEL[name]=$(lspci | grep -i 'vga\|3d\|display' | grep -i 'intel' | head -1 | sed 's/.*: //')
        
        if echo "${GPU_INTEL[name]}" | grep -iqE 'arc|a[3-7][0-9]0'; then
            GPU_INTEL[is_arc]=true
        fi
        
        if [[ "${GPU_NVIDIA[found]}" == false && "${GPU_AMD[found]}" == false ]]; then
            GPU_TYPE="intel"
        fi
    fi
}

detect_all_gpus() {
    log_step "${L[detecting_gpus]}"
    
    detect_nvidia
    detect_amd
    detect_intel
    
    log_success "${L[primary_gpu]}: ${GPU_TYPE^^}"
}

# ══════════════════════════════════════════════════════════════════════════════
#                            CONDA DETECTION
# ══════════════════════════════════════════════════════════════════════════════

declare -A CONDA_INFO

detect_conda() {
    log_step "${L[detecting_conda]}"
    
    CONDA_INFO[exe]=""
    CONDA_INFO[type]=""
    CONDA_INFO[path]=""
    
    # 1. Check PATH
    for cmd in mamba micromamba conda; do
        if command -v "$cmd" &>/dev/null; then
            CONDA_INFO[exe]=$(command -v "$cmd")
            CONDA_INFO[type]="$cmd"
            CONDA_INFO[path]="${CONDA_INFO[exe]}"
            log_success "${L[found]}: ${CONDA_INFO[type]} (${CONDA_INFO[path]})"
            return 0
        fi
    done
    
    # 2. Standard paths
    local standard_paths=(
        "$HOME/miniconda3/bin"
        "$HOME/miniforge3/bin"
        "$HOME/mambaforge/bin"
        "$HOME/anaconda3/bin"
        "$HOME/micromamba/bin"
        "$HOME/.local/share/micromamba/bin"
    )
    
    for path in "${standard_paths[@]}"; do
        for cmd in mamba micromamba conda; do
            if [[ -x "$path/$cmd" ]]; then
                CONDA_INFO[exe]="$path/$cmd"
                CONDA_INFO[type]="$cmd"
                CONDA_INFO[path]="$path/$cmd"
                log_success "${L[found]}: ${CONDA_INFO[type]} (${CONDA_INFO[path]})"
                return 0
            fi
        done
    done
    
    # 3. AUR paths (Arch)
    if [[ "${DISTRO_INFO[family]}" == "arch" ]]; then
        log_info "${L[searching_aur]}"
        
        local aur_paths=(
            "/opt/miniconda3/bin"
            "/opt/miniconda/bin"
            "/opt/anaconda3/bin"
            "/opt/anaconda/bin"
            "/opt/miniforge3/bin"
            "/opt/mambaforge/bin"
        )
        
        for path in "${aur_paths[@]}"; do
            for cmd in mamba conda; do
                if [[ -x "$path/$cmd" ]]; then
                    CONDA_INFO[exe]="$path/$cmd"
                    CONDA_INFO[type]="$cmd"
                    CONDA_INFO[path]="$path/$cmd"
                    log_success "${L[found]}: ${CONDA_INFO[type]} (${CONDA_INFO[path]}) [AUR]"
                    return 0
                fi
            done
        done
    fi
    
    # 4. CONDA_EXE environment variable
    if [[ -n "${CONDA_EXE:-}" && -x "$CONDA_EXE" ]]; then
        CONDA_INFO[exe]="$CONDA_EXE"
        CONDA_INFO[type]="conda"
        CONDA_INFO[path]="$CONDA_EXE"
        log_success "${L[found]}: conda (${CONDA_INFO[path]}) [CONDA_EXE]"
        return 0
    fi
    
    log_warn "${L[not_found]}"
    return 1
}

# ══════════════════════════════════════════════════════════════════════════════
#                         SYSTEM PACKAGES
# ══════════════════════════════════════════════════════════════════════════════

install_system_packages() {
    if [[ "${DISTRO_INFO[family]}" == "unknown" ]]; then
        log_warn "${L[unknown_distro]}"
        return 0
    fi
    
    local packages=()
    
    case "${DISTRO_INFO[family]}" in
        debian)
            packages=(
                libgl1-mesa-glx libegl1 libxcb1 libxcb-xinerama0 libxcb-cursor0
                libxkbcommon0 libxkbcommon-x11-0 libdbus-1-3 libfontconfig1
                build-essential git curl wget libsndfile1 libportaudio2
            )
            ;;
        arch)
            packages=(
                mesa libglvnd libxcb xcb-util xcb-util-cursor libxkbcommon
                libxkbcommon-x11 dbus fontconfig base-devel git curl wget
                libsndfile portaudio
            )
            ;;
        rhel)
            packages=(
                mesa-libGL mesa-libEGL libxcb libxkbcommon dbus-libs fontconfig
                gcc gcc-c++ make git curl wget libsndfile portaudio
            )
            ;;
    esac
    
    if [[ ${#packages[@]} -eq 0 ]]; then
        return 0
    fi
    
    log_step "${L[installing_packages]}"
    eval "${PKG_COMMANDS[update]}" 2>/dev/null || true
    
    local failed=()
    for pkg in "${packages[@]}"; do
        if ! eval "${PKG_COMMANDS[install]} $pkg" &>/dev/null; then
            failed+=("$pkg")
        fi
    done
    
    if [[ ${#failed[@]} -gt 0 ]]; then
        log_warn "${L[some_failed]}: ${failed[*]}"
    else
        log_success "${L[packages_installed]}"
    fi
}

# ══════════════════════════════════════════════════════════════════════════════
#                       ENVIRONMENT GENERATION
# ══════════════════════════════════════════════════════════════════════════════

get_env_filename() {
    local gpu_type="${1:-$GPU_TYPE}"
    echo "$SCRIPT_DIR/environment-lin-${gpu_type}.yml"
}

generate_environment() {
    local gpu_type="${1:-$GPU_TYPE}"
    local env_file=$(get_env_filename "$gpu_type")
    
    log_step "${L[generating]} environment-lin-${gpu_type}.yml..."
    
    # ══════════════════════════════════════════════════════════════════════════
    # Header
    # ══════════════════════════════════════════════════════════════════════════
    cat > "$env_file" << EOF
# ══════════════════════════════════════════════════════════════════════════════
#                     WORKSPACE ENVIRONMENT - LINUX ${gpu_type^^}
# ══════════════════════════════════════════════════════════════════════════════
# Generated: $(date '+%Y-%m-%d %H:%M:%S')
# Distro: ${DISTRO_INFO[pretty]:-Unknown}
# Script: v${VERSION}
EOF

    case "$gpu_type" in
        nvidia)
            echo "# GPU: ${GPU_NVIDIA[name]:-NVIDIA}" >> "$env_file"
            echo "# Driver: ${GPU_NVIDIA[driver]:-N/A}" >> "$env_file"
            echo "# CUDA: ${GPU_NVIDIA[cuda]}" >> "$env_file"
            ;;
        amd)
            echo "# GPU: ${GPU_AMD[name]:-AMD}" >> "$env_file"
            echo "# ROCm: ${GPU_AMD[rocm]:-N/A}" >> "$env_file"
            ;;
        intel)
            echo "# GPU: ${GPU_INTEL[name]:-Intel}" >> "$env_file"
            ;;
        cpu)
            echo "# Mode: CPU Only" >> "$env_file"
            ;;
    esac
    
    echo "# ══════════════════════════════════════════════════════════════════════════════" >> "$env_file"

    # ══════════════════════════════════════════════════════════════════════════
    # Channels
    # ══════════════════════════════════════════════════════════════════════════
    case "$gpu_type" in
        nvidia)
            cat >> "$env_file" << 'EOF'

name: workspace
channels:
  - nvidia
  - pytorch
  - conda-forge
  - defaults

EOF
            ;;
        *)
            cat >> "$env_file" << 'EOF'

name: workspace
channels:
  - pytorch
  - conda-forge
  - defaults

EOF
            ;;
    esac

    # ══════════════════════════════════════════════════════════════════════════
    # Core Dependencies
    # ══════════════════════════════════════════════════════════════════════════
    cat >> "$env_file" << 'EOF'
dependencies:
  # ═══════════════════════════════════════════════════════════════════════════
  #                                 CORE
  # ═══════════════════════════════════════════════════════════════════════════
  - python=3.10
  - pip
  - numpy
  - pandas
  - polars
  - pyarrow
  - duckdb
  - orjson
  - xxhash

EOF

    # ══════════════════════════════════════════════════════════════════════════
    # AI Section (GPU-specific)
    # ══════════════════════════════════════════════════════════════════════════
    case "$gpu_type" in
        nvidia)
            cat >> "$env_file" << EOF
  # ═══════════════════════════════════════════════════════════════════════════
  #                        AI & ML (NVIDIA CUDA ${GPU_NVIDIA[cuda]})
  # ═══════════════════════════════════════════════════════════════════════════
  - pytorch::pytorch
  - pytorch::torchvision
  - pytorch::torchaudio
  - pytorch::pytorch-cuda=${GPU_NVIDIA[cuda]}
  - faiss-gpu

EOF
            ;;
        amd)
            cat >> "$env_file" << 'EOF'
  # ═══════════════════════════════════════════════════════════════════════════
  #                           AI & ML (AMD ROCm)
  # ═══════════════════════════════════════════════════════════════════════════
  # NOTE: After env activation, install ROCm PyTorch:
  # pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
  - pytorch::pytorch
  - pytorch::torchvision
  - pytorch::torchaudio
  - pytorch::cpuonly
  - faiss-cpu

EOF
            ;;
        intel)
            cat >> "$env_file" << 'EOF'
  # ═══════════════════════════════════════════════════════════════════════════
  #                          AI & ML (Intel oneAPI)
  # ═══════════════════════════════════════════════════════════════════════════
  - pytorch::pytorch
  - pytorch::torchvision
  - pytorch::torchaudio
  - pytorch::cpuonly
  - faiss-cpu
  - mkl

EOF
            ;;
        cpu)
            cat >> "$env_file" << 'EOF'
  # ═══════════════════════════════════════════════════════════════════════════
  #                             AI & ML (CPU)
  # ═══════════════════════════════════════════════════════════════════════════
  - pytorch::pytorch
  - pytorch::torchvision
  - pytorch::torchaudio
  - pytorch::cpuonly
  - faiss-cpu

EOF
            ;;
    esac

    # ══════════════════════════════════════════════════════════════════════════
    # System & Build Tools
    # ══════════════════════════════════════════════════════════════════════════
    cat >> "$env_file" << 'EOF'
  # ═══════════════════════════════════════════════════════════════════════════
  #                            SYSTEM & BUILD
  # ═══════════════════════════════════════════════════════════════════════════
  - psutil
  - cmake
  - ninja
  - patchelf

  # ═══════════════════════════════════════════════════════════════════════════
  #                              PIP PACKAGES
  # ═══════════════════════════════════════════════════════════════════════════
  - pip:
EOF

    # ══════════════════════════════════════════════════════════════════════════
    # GPU-specific pip packages
    # ══════════════════════════════════════════════════════════════════════════
    case "$gpu_type" in
        nvidia)
            cat >> "$env_file" << 'EOF'
      # ─────────────────────────────────────────────────────────────────────────
      #                            NVIDIA Specific
      # ─────────────────────────────────────────────────────────────────────────
      - bitsandbytes>=0.41.0
      - onnxruntime-gpu
      - nvidia-ml-py

EOF
            ;;
        amd)
            cat >> "$env_file" << 'EOF'
      # ─────────────────────────────────────────────────────────────────────────
      #                             AMD Specific
      # ─────────────────────────────────────────────────────────────────────────
      # Install ROCm PyTorch after activation:
      # pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
      - onnxruntime

EOF
            ;;
        intel)
            cat >> "$env_file" << 'EOF'
      # ─────────────────────────────────────────────────────────────────────────
      #                            Intel Specific
      # ─────────────────────────────────────────────────────────────────────────
      - intel-extension-for-pytorch
      - onnxruntime
      - openvino

EOF
            ;;
        cpu)
            cat >> "$env_file" << 'EOF'
      # ─────────────────────────────────────────────────────────────────────────
      #                             CPU Runtime
      # ─────────────────────────────────────────────────────────────────────────
      - onnxruntime

EOF
            ;;
    esac

    # ══════════════════════════════════════════════════════════════════════════
    # Common pip packages
    # ══════════════════════════════════════════════════════════════════════════
    cat >> "$env_file" << 'EOF'
      # ─────────────────────────────────────────────────────────────────────────
      #                           P2P / Torrent
      # ─────────────────────────────────────────────────────────────────────────
      - libtorrent==2.0.11

      # ─────────────────────────────────────────────────────────────────────────
      #                             Networking
      # ─────────────────────────────────────────────────────────────────────────
      - zeroconf
      - aioquic
      - pyroute2
      - cryptography>=41.0.0
      - netifaces

      # ─────────────────────────────────────────────────────────────────────────
      #                         Qt6 + WebEngine
      # ─────────────────────────────────────────────────────────────────────────
      - PyQt6>=6.5.0
      - PyQt6-WebEngine>=6.5.0
      - PyQt6-Qt6>=6.5.0
      - PyQt6-WebEngine-Qt6>=6.5.0

      # ─────────────────────────────────────────────────────────────────────────
      #                        Distributed Compute
      # ─────────────────────────────────────────────────────────────────────────
      - ray[default]>=2.7.0
      - lz4
      - accelerate>=0.24.0

      # ─────────────────────────────────────────────────────────────────────────
      #                            UI & Utils
      # ─────────────────────────────────────────────────────────────────────────
      - qasync
      - NodeGraphQt
      - pytablericons
      - superqt
      - playwright
      - watchdog

      # ─────────────────────────────────────────────────────────────────────────
      #                           Data & ML Tools
      # ─────────────────────────────────────────────────────────────────────────
      - transformers>=4.35.0
      - robyn
      - psqlpy
      - markdown
      - plotly

      # ─────────────────────────────────────────────────────────────────────────
      #                              Build (ye)
      # ─────────────────────────────────────────────────────────────────────────
      - pyinstaller
EOF

    log_success "${L[generated]}: $env_file"
    
    # Create symlink
    ln -sf "$(basename "$env_file")" "$SCRIPT_DIR/environment.yml" 2>/dev/null || \
        cp "$env_file" "$SCRIPT_DIR/environment.yml"
    echo -e "   ${GRAY}→ environment.yml${NC}"
}

# ══════════════════════════════════════════════════════════════════════════════
#                          CONDA OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

install_micromamba() {
    log_step "${L[installing_micromamba]}"
    
    local MAMBA_ROOT="${HOME}/.local/share/micromamba"
    mkdir -p "$MAMBA_ROOT"
    
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | \
        tar -xvj -C "$MAMBA_ROOT" --strip-components=1 bin/micromamba
    
    "$MAMBA_ROOT/bin/micromamba" shell init -s bash -p "$MAMBA_ROOT" 2>/dev/null || true
    "$MAMBA_ROOT/bin/micromamba" shell init -s zsh -p "$MAMBA_ROOT" 2>/dev/null || true
    
    CONDA_INFO[exe]="$MAMBA_ROOT/bin/micromamba"
    CONDA_INFO[type]="micromamba"
    CONDA_INFO[path]="$MAMBA_ROOT/bin/micromamba"
    
    log_success "${L[micromamba_installed]} $MAMBA_ROOT"
    log_warn "${L[restart_shell]}"
}

create_environment() {
    local gpu_type="${1:-$GPU_TYPE}"
    local env_file=$(get_env_filename "$gpu_type")
    
    if [[ -z "${CONDA_INFO[exe]}" ]]; then
        log_error "${L[no_conda]}"
        return 1
    fi
    
    if [[ ! -f "$env_file" ]]; then
        generate_environment "$gpu_type"
    fi
    
    log_step "${L[creating_env]} 'workspace'..."
    
    # Suppress OpenSSL warnings
    export CRYPTOGRAPHY_OPENSSL_NO_LEGACY=1
    
    # Remove existing env
    ${CONDA_INFO[exe]} env remove -n workspace -y 2>/dev/null || true
    
    # Create new env
    if ${CONDA_INFO[exe]} env create -f "$env_file" -n workspace; then
        log_success "${L[env_created]}"
        echo ""
        echo -e "${GREEN}   ${L[activate_with]}${NC}"
        echo -e "${CYAN}   conda activate workspace${NC}"
        
        # AMD ROCm hint
        if [[ "$gpu_type" == "amd" ]]; then
            echo ""
            echo -e "${YELLOW}   AMD ROCm PyTorch (run after activation):${NC}"
            echo -e "${CYAN}   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0${NC}"
        fi
        return 0
    else
        log_error "${L[failed_create]}"
        return 1
    fi
}

ensure_conda() {
    if [[ -z "${CONDA_INFO[exe]}" ]]; then
        echo ""
        read -p "${L[install_micromamba_q]} [Y/n] " yn
        if [[ "${yn:-y}" =~ ^[Yy] ]]; then
            install_micromamba
        fi
    fi
}

# ══════════════════════════════════════════════════════════════════════════════
#                               USER INTERFACE
# ══════════════════════════════════════════════════════════════════════════════

print_banner() {
    echo ""
    echo -e "${PURPLE}"
    cat << 'EOF'
    ╦ ╦╔═╗╦═╗╦╔═╔═╗╔═╗╔═╗╔═╗╔═╗  ╔═╗╔═╗╔╦╗╦ ╦╔═╗
    ║║║║ ║╠╦╝╠╩╗╚═╗╠═╝╠═╣║  ║╣   ╚═╗║╣  ║ ║ ║╠═╝
    ╚╩╝╚═╝╩╚═╩ ╩╚═╝╩  ╩ ╩╚═╝╚═╝  ╚═╝╚═╝ ╩ ╚═╝╩  
EOF
    echo -e "${NC}"
    echo -e "${GRAY}    Universal Environment Setup v${VERSION}${NC}"
    echo -e "${GRAY}    Supports: NVIDIA • AMD • Intel • CPU${NC}"
    echo ""
}

print_system_info() {
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}                      ${L[system_info]}${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Distribution
    echo -e "  ${BLUE}${ICON_CPU} ${L[distribution]}${NC}"
    echo -e "     ${WHITE}${DISTRO_INFO[pretty]}${NC} (${PKG_COMMANDS[manager]})"
    echo ""
    
    # Graphics
    echo -e "  ${BLUE}${ICON_GPU} ${L[graphics]}${NC}"
    
    if [[ "${GPU_NVIDIA[found]}" == true ]]; then
        echo -e "     ${GREEN}NVIDIA:${NC} ${GPU_NVIDIA[name]}"
        echo -e "             ${L[driver]}: ${GPU_NVIDIA[driver]}, CUDA: ${GPU_NVIDIA[cuda]}"
    fi
    
    if [[ "${GPU_AMD[found]}" == true ]]; then
        echo -e "     ${RED}AMD:${NC} ${GPU_AMD[name]}"
        echo -e "             ROCm: ${GPU_AMD[rocm]:-${L[not_found]}}"
    fi
    
    if [[ "${GPU_INTEL[found]}" == true ]]; then
        echo -e "     ${BLUE}Intel:${NC} ${GPU_INTEL[name]}"
    fi
    
    if [[ "${GPU_NVIDIA[found]}" == false && "${GPU_AMD[found]}" == false && "${GPU_INTEL[found]}" == false ]]; then
        echo -e "     ${GRAY}${L[no_gpu]}${NC}"
    fi
    
    echo ""
    echo -e "  ${WHITE}→ ${L[will_use]}: ${GPU_TYPE^^}${NC} (environment-lin-${GPU_TYPE}.yml)"
    echo ""
    
    # Conda/Mamba
    echo -e "  ${BLUE}${ICON_PKG} ${L[conda_mamba]}${NC}"
    if [[ -n "${CONDA_INFO[exe]}" ]]; then
        echo -e "     ${CONDA_INFO[type]}: ${CONDA_INFO[path]}"
    else
        echo -e "     ${YELLOW}${L[not_found]}${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
}

print_menu() {
    echo ""
    echo -e "${WHITE}${L[what_to_do]}${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} ${L[menu_1]}"
    echo -e "  ${GREEN}2)${NC} ${L[menu_2]}"
    echo -e "  ${GREEN}3)${NC} ${L[menu_3]}"
    echo ""
    echo -e "  ${CYAN}4)${NC} ${L[menu_4]}"
    echo -e "  ${CYAN}5)${NC} ${L[menu_5]}"
    echo -e "  ${CYAN}6)${NC} ${L[menu_6]}"
    echo -e "  ${CYAN}7)${NC} ${L[menu_7]}"
    echo ""
    echo -e "  ${GRAY}0)${NC} ${L[menu_0]}"
    echo ""
}

select_gpu_override() {
    echo ""
    echo -e "${WHITE}${L[select_gpu]}${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} NVIDIA (CUDA)"
    echo -e "  ${RED}2)${NC} AMD (ROCm)"
    echo -e "  ${BLUE}3)${NC} Intel (XPU/oneAPI)"
    echo -e "  ${GRAY}4)${NC} CPU only"
    echo ""
    
    read -p "${L[choice]} [1-4]: " choice
    
    case "$choice" in
        1) GPU_TYPE="nvidia" ;;
        2) GPU_TYPE="amd" ;;
        3) GPU_TYPE="intel" ;;
        4) GPU_TYPE="cpu" ;;
    esac
    
    echo -e "${GREEN}${ICON_OK}${NC} ${L[selected]}: ${GPU_TYPE^^}"
}

# ══════════════════════════════════════════════════════════════════════════════
#                                  MAIN
# ══════════════════════════════════════════════════════════════════════════════

main() {
    print_banner
    select_language
    
    detect_distro
    detect_all_gpus
    detect_conda
    
    print_system_info
    
    # CLI arguments
    case "${1:-}" in
        --quick)
            generate_environment
            ensure_conda
            [[ -n "${CONDA_INFO[exe]}" ]] && create_environment
            exit 0
            ;;
        --full)
            install_system_packages
            generate_environment
            ensure_conda
            if [[ -n "${CONDA_INFO[exe]}" ]] && create_environment; then
                log_step "${L[installing_playwright]}"
                ${CONDA_INFO[exe]} run -n workspace playwright install chromium 2>/dev/null || true
            fi
            exit 0
            ;;
        --generate)
            generate_environment "${2:-$GPU_TYPE}"
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [--quick|--full|--generate [TYPE]|--help]"
            echo ""
            echo "Options:"
            echo "  --quick              Generate env file and create conda environment"
            echo "  --full               Full setup including system packages and playwright"
            echo "  --generate [TYPE]    Only generate environment file (nvidia/amd/intel/cpu)"
            echo "  --help, -h           Show this help"
            exit 0
            ;;
    esac
    
    # Interactive mode
    while true; do
        print_menu
        read -p "${L[choice]}: " choice
        
        case "$choice" in
            1)
                generate_environment
                ensure_conda
                [[ -n "${CONDA_INFO[exe]}" ]] && create_environment
                ;;
            2)
                install_system_packages
                generate_environment
                ensure_conda
                [[ -n "${CONDA_INFO[exe]}" ]] && create_environment
                ;;
            3)
                install_system_packages
                generate_environment
                ensure_conda
                if [[ -n "${CONDA_INFO[exe]}" ]] && create_environment; then
                    log_step "${L[installing_playwright]}"
                    ${CONDA_INFO[exe]} run -n workspace playwright install chromium 2>/dev/null || true
                fi
                ;;
            4)
                select_gpu_override
                ;;
            5)
                generate_environment
                ;;
            6)
                create_environment
                ;;
            7)
                install_micromamba
                detect_conda
                ;;
            0|q|exit)
                log_info "${L[goodbye]}"
                exit 0
                ;;
            *)
                log_warn "${L[invalid_choice]}"
                ;;
        esac
        
        echo ""
        read -p "${L[press_enter]}"
        print_system_info
    done
}

main "$@"
