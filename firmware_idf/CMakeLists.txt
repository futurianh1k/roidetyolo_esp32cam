# ESP-IDF Project CMakeLists.txt
# Core S3 Management System - ESP-IDF Version

cmake_minimum_required(VERSION 3.16)

# Project version
set(PROJECT_VER "1.0.0")

# Disable specific warnings
add_compile_options(-Wno-missing-field-initializers)

# Include ESP-IDF build system
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# Project name
project(cores3-management)

