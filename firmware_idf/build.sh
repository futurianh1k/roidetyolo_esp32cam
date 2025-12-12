#!/bin/bash
# ESP-IDF Build Script for Linux
# Usage: ./build.sh [options]

set -e  # Exit on error

# Default values
IDF_PATH="${IDF_PATH:-}"
TARGET="esp32s3"
PORT=""
FLASH=false
MONITOR=false
CLEAN=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --idf-path)
            IDF_PATH="$2"
            shift 2
            ;;
        --target)
            TARGET="$2"
            shift 2
            ;;
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --flash|-f)
            FLASH=true
            shift
            ;;
        --monitor|-m)
            MONITOR=true
            shift
            ;;
        --clean|-c)
            CLEAN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --idf-path PATH    ESP-IDF installation path"
            echo "  --target TARGET    Target chip (default: esp32s3)"
            echo "  --port PORT        Serial port (e.g., /dev/ttyUSB0)"
            echo "  --flash, -f        Flash firmware after build"
            echo "  --monitor, -m      Start serial monitor after flash"
            echo "  --clean, -c        Clean build before building"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Build only"
            echo "  $0 --flash                           # Build and flash"
            echo "  $0 --flash --monitor                 # Build, flash, and monitor"
            echo "  $0 --port /dev/ttyUSB0 --flash       # Build and flash to specific port"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}ESP-IDF Build Script${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Find ESP-IDF path
if [ -z "$IDF_PATH" ]; then
    # Check IDF_PATH environment variable
    if [ -n "$IDF_PATH" ] && [ -d "$IDF_PATH" ]; then
        echo -e "${CYAN}[INFO] Using IDF_PATH: $IDF_PATH${NC}"
    # Check common installation paths
    elif [ -d "$HOME/esp/esp-idf" ]; then
        IDF_PATH="$HOME/esp/esp-idf"
    elif [ -d "$HOME/.espressif/frameworks/esp-idf-v5.4" ]; then
        IDF_PATH="$HOME/.espressif/frameworks/esp-idf-v5.4"
    elif [ -d "$HOME/.espressif/frameworks/esp-idf-v5.3" ]; then
        IDF_PATH="$HOME/.espressif/frameworks/esp-idf-v5.3"
    elif [ -d "/opt/esp/idf" ]; then
        IDF_PATH="/opt/esp/idf"
    else
        echo -e "${RED}ERROR: ESP-IDF path not found${NC}"
        echo ""
        echo -e "${YELLOW}Please specify ESP-IDF path:${NC}"
        echo -e "${CYAN}  $0 --idf-path /path/to/esp-idf${NC}"
        echo ""
        echo -e "${YELLOW}Or set IDF_PATH environment variable:${NC}"
        echo -e "${CYAN}  export IDF_PATH=/path/to/esp-idf${NC}"
        echo ""
        echo -e "${YELLOW}Common locations:${NC}"
        echo -e "${GRAY}  - $HOME/esp/esp-idf${NC}"
        echo -e "${GRAY}  - $HOME/.espressif/frameworks/esp-idf-v5.4${NC}"
        echo -e "${GRAY}  - /opt/esp/idf${NC}"
        exit 1
    fi
fi

# Verify ESP-IDF path
if [ ! -d "$IDF_PATH" ]; then
    echo -e "${RED}ERROR: ESP-IDF path does not exist: $IDF_PATH${NC}"
    exit 1
fi

# Check for export.sh
EXPORT_SCRIPT="$IDF_PATH/export.sh"
if [ ! -f "$EXPORT_SCRIPT" ]; then
    echo -e "${RED}ERROR: export.sh not found in: $IDF_PATH${NC}"
    echo -e "${YELLOW}   Please check ESP-IDF installation path${NC}"
    exit 1
fi

# Setup ESP-IDF environment
echo -e "${YELLOW}[1] Setting up ESP-IDF environment...${NC}"
echo -e "${GRAY}   ESP-IDF path: $IDF_PATH${NC}"
echo -e "${GRAY}   Found export.sh: $EXPORT_SCRIPT${NC}"

# Source ESP-IDF environment
source "$EXPORT_SCRIPT"

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to export ESP-IDF environment${NC}"
    exit 1
fi

echo -e "${GREEN}OK: ESP-IDF environment setup complete${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo ""
echo -e "${YELLOW}[2] Project directory: $SCRIPT_DIR${NC}"

# Clean build or remove incomplete build directory
if [ "$CLEAN" = true ] || [ -d "build" ]; then
    echo ""
    if [ "$CLEAN" = true ]; then
        echo -e "${YELLOW}[3] Running clean build...${NC}"
        if [ -f "build/CMakeCache.txt" ] || [ -f "build/build.ninja" ]; then
            # Valid CMake build directory, use fullclean
            idf.py fullclean || echo -e "${YELLOW}WARNING: Clean build warning (continuing)${NC}"
        else
            # Incomplete build directory, remove it
            echo -e "${GRAY}   Removing incomplete build directory...${NC}"
            rm -rf build
        fi
    else
        # Check if build directory is valid
        if [ -d "build" ] && [ ! -f "build/CMakeCache.txt" ] && [ ! -f "build/build.ninja" ]; then
            echo -e "${YELLOW}[3] Removing incomplete build directory...${NC}"
            rm -rf build
        fi
    fi
fi

# Set target
echo ""
echo -e "${YELLOW}[4] Setting target: $TARGET${NC}"
idf.py set-target "$TARGET"

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to set target${NC}"
    exit 1
fi

# Build
echo ""
echo -e "${YELLOW}[5] Building...${NC}"
echo -e "${GRAY}   (This may take several minutes)${NC}"
idf.py build

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}OK: Build successful!${NC}"
    echo ""
    echo -e "${CYAN}Build results:${NC}"
    BIN_FILE="build/cores3-management.bin"
    if [ -f "$BIN_FILE" ]; then
        FILE_SIZE=$(du -h "$BIN_FILE" | cut -f1)
        echo -e "${CYAN}   Firmware: $BIN_FILE ($FILE_SIZE)${NC}"
    fi
    
    # Flash
    if [ "$FLASH" = true ]; then
        echo ""
        echo -e "${YELLOW}[6] Flashing firmware...${NC}"
        if [ -n "$PORT" ]; then
            idf.py -p "$PORT" flash
        else
            echo -e "${GRAY}   Auto-detecting port...${NC}"
            idf.py flash
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}OK: Flash complete${NC}"
        else
            echo -e "${RED}ERROR: Flash failed${NC}"
            exit 1
        fi
    fi
    
    # Monitor
    if [ "$MONITOR" = true ]; then
        echo ""
        echo -e "${YELLOW}[7] Starting serial monitor...${NC}"
        echo -e "${GRAY}   Exit: Ctrl+]${NC}"
        if [ -n "$PORT" ]; then
            idf.py -p "$PORT" monitor
        else
            idf.py monitor
        fi
    fi
else
    echo ""
    echo -e "${RED}ERROR: Build failed${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "${GRAY}1. Check ESP-IDF environment variables${NC}"
    echo -e "${GRAY}2. Check component dependencies (idf_component.yml)${NC}"
    echo -e "${GRAY}3. Check CMakeLists.txt files${NC}"
    echo -e "${GRAY}4. Check detailed log: idf.py build -v${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}Complete${NC}"
echo -e "${CYAN}============================================================${NC}"

