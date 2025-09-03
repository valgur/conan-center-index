# Replacement for https://github.com/NVIDIA-AI-IOT/Lidar_AI_Solution/blob/master/libraries/cuOSD/Makefile
cmake_minimum_required(VERSION 3.18)
project(cuosd LANGUAGES CXX CUDA)

option(ENABLE_PANGO "Enable PangoCairo text backend" OFF)
option(ENABLE_STB   "Enable stb_truetype text backend" OFF)

set(CMAKE_CXX_STANDARD 17 CACHE STRING "C++ standard to use")
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS TRUE)

add_library(cuosd
    src/cuosd.cpp
    src/cuosd_kernel.cu
    src/textbackend/backend.cpp
    src/textbackend/pango-cairo.cpp
    src/textbackend/stb.cpp
)
target_include_directories(cuosd PUBLIC src)
target_compile_definitions(cuosd PRIVATE _USE_MATH_DEFINES)

find_package(CUDAToolkit REQUIRED)
target_link_libraries(cuosd PUBLIC CUDA::cudart)

if(ENABLE_PANGO)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(pangocairo REQUIRED IMPORTED_TARGET pangocairo)
    target_link_libraries(cuosd PUBLIC PkgConfig::pangocairo)
    target_compile_definitions(cuosd PUBLIC ENABLE_TEXT_BACKEND_PANGO)
endif()

if(ENABLE_STB)
    find_package(stb REQUIRED)
    target_link_libraries(cuosd PUBLIC stb::stb)
    target_compile_definitions(cuosd PUBLIC ENABLE_TEXT_BACKEND_STB)
endif()

if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(cuosd PRIVATE -Wall -Wextra -Wmissing-declarations)
endif()

install(TARGETS cuosd
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
)
install(FILES
    src/cuosd.h
    src/cuosd_kernel.h
    DESTINATION include
)
