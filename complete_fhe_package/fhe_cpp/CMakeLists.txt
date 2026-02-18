cmake_minimum_required(VERSION 3.12)
project(fhe_fast_mult)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native")

# Find Python and pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# Source files
set(SOURCES
    ntt.cpp
    bfv_mult.cpp
    bindings.cpp
)

# Create Python module
pybind11_add_module(fhe_fast_mult ${SOURCES})

# Link libraries
target_link_libraries(fhe_fast_mult PRIVATE)

# Installation
install(TARGETS fhe_fast_mult
        LIBRARY DESTINATION ${Python3_SITELIB})
