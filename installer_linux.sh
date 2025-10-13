#!/bin/bash
# Installer Script for TTS Library - Linux
# Usage: ./installer_linux.sh

# Farben definieren
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log-Datei erstellen
mkdir -p logs  # Verzeichnis sicher anlegen
LOG_FILE="logs/installer.log"

# Log-Funktion
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    echo "[$timestamp] [$level] $message"
}

# Fehler-Funktion
error_exit() {
    local message=$1
    log_message "ERROR" "$message"
    echo -e "${RED}Error: $message${NC}" >&2
    exit 1
}

# Erfolg-Funktion
success() {
    local message=$1
    log_message "SUCCESS" "$message"
    echo -e "${GREEN} $message${NC}"
}

# Warnung-Funktion
warning() {
    local message=$1
    log_message "WARNING" "$message"
    echo -e "${YELLOW} $message${NC}"
}

# Info-Funktion
info() {
    local message=$1
    log_message "INFO" "$message"
    echo -e "${BLUE} $message${NC}"
}

echo -e "${YELLOW}┌──────────────────────────────────┐${NC}"
echo -e "${YELLOW}│ TTS Library Installation Script! │${NC}"
echo -e "${YELLOW}└──────────────────────────────────┘${NC}"

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    error_exit "This script is designed for Linux systems only."
fi

# Ensure bin directory exists
mkdir -p bin || error_exit "Failed to create 'bin' directory."

info "Installing required system packages..."
info "This may require your password for sudo access."

# Install required system packages
sudo apt update || error_exit "Failed to update package list"
sudo apt install -y portaudio19-dev espeak-ng-data || error_exit "Failed to install required system packages (portaudio19-dev, espeak-ng-data)"

success "System packages installed successfully."

# Funktion zur automatischen Installation von Python 3.12
install_python_312() {
    info "Python 3.12 not found. Attempting to install..."

    # Prüfen welche Distribution wir haben
    if command -v apt &> /dev/null; then
        # Ubuntu/Debian
        info "Detected Debian/Ubuntu system. Installing dependencies..."
        sudo apt update || error_exit "Failed to update package list"
        sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev || error_exit "Failed to install build dependencies"

        info "Downloading Python 3.12..."
        cd /tmp
        wget https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tgz || error_exit "Failed to download Python 3.12"
        tar -xf Python-3.12.4.tgz
        cd Python-3.12.4

        info "Compiling Python 3.12..."
        ./configure --enable-optimizations || error_exit "Failed to configure Python build"
        make -j $(nproc) || error_exit "Failed to compile Python 3.12"

        info "Installing Python 3.12..."
        sudo make altinstall || error_exit "Failed to install Python 3.12"

        # Löschen der temporären Dateien
        cd /tmp
        rm -rf Python-3.12.4*

        success "Python 3.12 installed successfully!"
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL/Fedora
        info "Detected RedHat/CentOS system. Installing dependencies..."
        sudo yum groupinstall -y "Development Tools" || error_exit "Failed to install development tools"
        sudo yum install -y openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel wget || error_exit "Failed to install build dependencies"

        info "Downloading Python 3.12..."
        cd /tmp
        wget https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tgz || error_exit "Failed to download Python 3.12"
        tar -xf Python-3.12.4.tgz
        cd Python-3.12.4

        info "Compiling Python 3.12..."
        ./configure --enable-optimizations || error_exit "Failed to configure Python build"
        make -j $(nproc) || error_exit "Failed to compile Python 3.12"

        info "Installing Python 3.12..."
        sudo make altinstall || error_exit "Failed to install Python 3.12"

        # Löschen der temporären Dateien
        cd /tmp
        rm -rf Python-3.12.4*

        success "Python 3.12 installed successfully!"
    else
        error_exit "Unsupported Linux distribution. Please install Python 3.12 manually from https://www.python.org"
    fi
}

# Check Python 3.12 installation
if command -v python3.12 &> /dev/null; then
    info "Python 3.12 is already installed"
    PYTHON_VERSION=$(python3.12 --version 2>&1)
    info "Using $PYTHON_VERSION"
elif command -v python3 &> /dev/null; then
    # Prüfen, ob python3 die richtige Version ist
    PYTHON_VERSION=$(python3 --version 2>&1)
    if [[ "$PYTHON_VERSION" == *"3.12."* ]]; then
        info "Python 3.12 found as python3"
        PYTHON_CMD="python3"
    else
        info "Python 3.12 not found, but python3 exists with version $PYTHON_VERSION"
        install_python_312
        PYTHON_CMD="python3.12"
    fi
else
    # Python 3 nicht vorhanden, installiere Python 3.12
    install_python_312
    PYTHON_CMD="python3.12"
fi

# Prüfen, ob Python 3.12 jetzt verfügbar ist
if ! command -v python3.12 &> /dev/null; then
    error_exit "Python 3.12 installation failed or not found in PATH"
fi

info "Proceeding with installation using Python 3.12..."

# Erstelle virtuelle Umgebung mit Python 3.12
info "Creating virtual environment with Python 3.12..."
python3.12 -m venv bin/ai_env || error_exit "Failed to create virtual environment"

success "Virtual environment created successfully."

# Activate virtual environment
source bin/ai_env/bin/activate

info "Installing required Python packages..."
pip install --upgrade pip || error_exit "Failed to upgrade pip"

# Install package using venv's pip
bin/ai_env/bin/pip install . || error_exit "Failed to install TTS library"

# Run post-install script only if it exists
if [[ -f "post_install.py" ]]; then
    info "Running post-installation setup..."
    python post_install.py || warning "Post-installation script failed, but installation may still work"
else
    info "No post-installation script found. Skipping."
fi

# Deaktiviere virtuelle Umgebung
deactivate

success "Installation completed successfully!"

echo ""
echo -e "${YELLOW}┌──────────────────────────────────┐${NC}"
echo -e "${YELLOW}│      Installation Summary:       │${NC}"
echo -e "${YELLOW}└──────────────────────────────────┘${NC}"
echo -e "${GREEN}1. System dependencies installed:${NC}"
echo -e "${GREEN}   - Build tools${NC}"
echo -e "${GREEN}   - Audio libraries${NC}"
echo -e "${GREEN}2. Python 3.12 installed${NC}"
echo -e "${GREEN}3. Virtual environment created at: bin/ai_env${NC}"
echo -e "${GREEN}4. TTS library installed in virtual environment${NC}"
echo ""
echo -e "${BLUE}To use the TTS library, activate the virtual environment:${NC}"
echo -e "${BLUE}  source bin/ai_env/bin/activate${NC}"
echo ""
echo -e "${BLUE}Then run your TTS application:${NC}"
echo -e "${BLUE}  python bin/cli_example_tts.py${NC}"
echo ""
echo -e "${YELLOW}Installation complete! Enjoy your TTS setup!${NC}"

log_message "SUCCESS" "Linux installation completed successfully"
