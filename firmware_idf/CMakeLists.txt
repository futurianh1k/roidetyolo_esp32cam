# ESP-IDF Project CMakeLists.txt
# Core S3 Management System - ESP-IDF Version

cmake_minimum_required(VERSION 3.16)

# Project version
set(PROJECT_VER "1.0.0")

# Make local BSP component available to this project.
# Must be set BEFORE including ESP-IDF's project.cmake.
set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/cores3bsp/m5stack_core_s3"
)

# Disable specific warnings
add_compile_options(-Wno-missing-field-initializers)

# Include ESP-IDF build system
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# Project name
project(cores3-management)

