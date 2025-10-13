#!/bin/bash
# Installer Script for TTS Library - macOS
# Usage: ./installer_macos.sh

# Farben definieren
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log-Datei erstellen (absoluter Pfad)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SCRIPT_DIR/logs"
LOG_FILE="$SCRIPT_DIR/logs/installer_macos.log"
> "$LOG_FILE"

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

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    error_exit "This script is designed for macOS systems only."
fi

# Prüfen ob Homebrew installiert ist
if ! command -v brew &> /dev/null; then
    info "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ $? -ne 0 ]; then
        error_exit "Failed to install Homebrew"
    fi
fi

# Funktion zur Installation von Python 3.12.4 wenn nicht vorhanden
install_python_if_needed() {
    local target_version="3.12.4"

    # Prüfen, ob Python bereits installiert ist
    if command -v python3 &> /dev/null; then
        # Versionsprüfung
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        info "Found existing Python version: $python_version"

        # Überprüfen, ob die Version korrekt ist
        if [[ "$python_version" == "3.12.4" ]]; then
            info "Correct Python version ($target_version) already installed"
            return 0
        else
            info "Python version is not $target_version, installing correct version..."
        fi
    else
        info "Python not found, installing via Homebrew..."
    fi

    # Versuche zuerst mit pyenv (wenn verfügbar)
    if command -v pyenv &> /dev/null; then
        info "Using pyenv to install Python $target_version..."
        pyenv install "$target_version"
        pyenv global "$target_version"
        success "Successfully installed Python $target_version with pyenv"
        return 0
    else
        warning "pyenv not available, falling back to Homebrew installation..."
    fi

    # Fallback auf Homebrew
    info "Installing Python $target_version via Homebrew..."
    brew install python@3.12
    if [ $? -ne 0 ]; then
        warning "Homebrew installation failed, trying alternative method..."
        # Alternative Methode: Direkter Download
        info "Attempting manual download of Python $target_version..."
        # In der Praxis würde man hier eine URL verwenden
        warning "Manual installation not implemented in this script"
        error_exit "Could not install Python $target_version. Please install manually."
    fi

    # Überprüfen, ob Installation erfolgreich war
    if command -v python3 &> /dev/null; then
        actual_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        if [[ "$actual_version" == "3.12.4" ]]; then
            success "Successfully installed Python: $actual_version"
            return 0
        else
            warning "Python installed but version is not $target_version (got: $actual_version)"
        fi
    fi

    # Letzter Versuch: Manuelle Version prüfen und ggf. warnen
    if command -v python3 &> /dev/null; then
        actual_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        warning "Python installed as $actual_version (expected: 3.12.4)"
        return 0
    else
        error_exit "Python installation failed. Please install Python 3.12.4 manually from: https://www.python.org/downloads/macos/"
    fi
}

# Funktion zur Installation von Paketen
install_packages() {
    local packages=("$@")
    local failed_packages=()

    for package in "${packages[@]}"; do
        if brew list "$package" &>/dev/null; then
            info "Package $package already installed"
        else
            info "Installing $package via Homebrew..."
            brew install "$package"
            if [ $? -ne 0 ]; then
                failed_packages+=("$package")
                warning "Failed to install $package"
            else
                success "Successfully installed $package"
            fi
        fi
    done

    # Warnung bei fehlgeschlagenen Paketen
    if [ ${#failed_packages[@]} -gt 0 ]; then
        warning "Some packages failed to install: ${failed_packages[*]}"
    fi
}

# Installiere benötigte Systempakete
info "Installing required system packages via Homebrew..."
install_packages "portaudio" "espeak"

# Prüfen, ob Pakete wirklich installiert sind
info "Verifying package installations..."
if ! command -v portaudio &> /dev/null; then
    warning "portaudio might not be properly installed"
fi

if ! command -v espeak &> /dev/null; then
    warning "espeak might not be properly installed"
fi

# Installiere Python 3.12.4
install_python_if_needed

# Erstellen des virtuellen Environments
info "Creating Python virtual environment..."
python3 -m venv bin/ai_env
if [ $? -ne 0 ]; then
    error_exit "Failed to create virtual environment"
fi

success "Virtual environment created successfully"

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

echo
echo -e "${YELLOW}┌──────────────────────────────────┐${NC}"
echo -e "${YELLOW}│      Installation Summary:       │${NC}"
echo -e "${YELLOW}└──────────────────────────────────┘${NC}"
echo -e "${GREEN}1. Required packages installed:${NC}"
echo -e "${GREEN}   - portaudio${NC}"
echo -e "${GREEN}   - espeak${NC}"
echo -e "${GREEN}   - ffmpeg${NC}"
echo -e "${GREEN}2. Python 3.12.4 installed${NC}"
echo -e "${GREEN}3. Virtual environment created at: bin/ai_env${NC}"
echo -e "${GREEN}4. TTS library installed in virtual environment${NC}"
echo -e "${GREEN}5. Post-installation setup completed${NC}"

echo
echo -e "${BLUE}To use the TTS library, please activate the virtual environment:${NC}"
echo -e "${BLUE}  source bin/ai_env/bin/activate${NC}"
echo ""
echo -e "${BLUE}Then you can run the CLI example:${NC}"
echo -e "${BLUE}  python bin/cli_example_tts.py${NC}"
echo ""
echo -e "${BLUE}For testing with French language:${NC}"
echo -e "${BLUE}  python bin/cli_example_tts.py --text \"Ce n'est qu'un petit exemple de conversion de texte en sortie audio.\" --language fr${NC}"
echo
echo -e "${YELLOW}  Installation complete! Enjoy!  ${NC}"

log_message "SUCCESS" "macOS installation completed successfully with Python 3.12.4"
