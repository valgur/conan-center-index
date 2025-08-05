include_guard()

# Find all packagages supported by FindCUDAToolkit.cmake as of CMake v4.0.3
foreach(pkg
        cudart cublas cudla cufile cufft curand cusolver cusparse cupti npp
        nvjpeg nvml-stubs nvptxcompiler nvrtc nvjitlink nvfatbin nvtx3 cuda-opencl
        nvcc-headers libcudacxx thrust cub)
    find_package(${pkg} QUIET)
    if(NOT ${pkg}_FOUND)
        continue()
    endif()
    list(APPEND CUDAToolkit_INCLUDE_DIRS ${${pkg}_INCLUDE_DIRS})
    if(EXISTS "${${pkg}_INCLUDE_DIR}/../lib")
        get_filename_component(_lib_dir "${${pkg}_INCLUDE_DIR}/../lib" ABSOLUTE)
        list(APPEND CUDAToolkit_LIBRARY_DIR "${_lib_dir}")
    endif()
    if(EXISTS "${${pkg}_INCLUDE_DIR}/../lib/stubs")
        get_filename_component(_lib_dir "${${pkg}_INCLUDE_DIR}/../lib/stubs" ABSOLUTE)
        list(APPEND CUDAToolkit_LIBRARY_DIR "${_lib_dir}")
    endif()
endforeach()

set(CUDAToolkit_BIN_DIR)
set(CUDAToolkit_TARGET_DIR)
set(CUDAToolkit_LIBRARY_ROOT)

if(FALSE AND DEFINED ENV{CUDACXX})
    set(CUDAToolkit_NVCC_EXECUTABLE "$ENV{CUDACXX}")
else()
    find_program(CUDAToolkit_NVCC_EXECUTABLE nvcc QUIET)
endif()
if(CUDAToolkit_NVCC_EXECUTABLE)
    # Parse nvcc version from nvcc --version output:
    #   nvcc: NVIDIA (R) Cuda compiler driver
    #   Copyright (c) 2005-2025 NVIDIA Corporation
    #   Built on Tue_May_27_02:21:03_PDT_2025
    #   Cuda compilation tools, release 12.9, V12.9.86
    #   Build cuda_12.9.r12.9/compiler.36037853_0
    execute_process(COMMAND ${CUDAToolkit_NVCC_EXECUTABLE} --version OUTPUT_VARIABLE _nvcc_version_output)
    if("${_nvcc_version_output}" MATCHES "release ([0-9]+\\.[0-9]+)," AND
       CMAKE_MATCH_1 STREQUAL "${CUDAToolkit_VERSION_MAJOR}.${CUDAToolkit_VERSION_MINOR}")
        get_filename_component(CUDAToolkit_BIN_DIR "${CUDAToolkit_NVCC_EXECUTABLE}" DIRECTORY)
        get_filename_component(CUDAToolkit_ROOT "${CUDAToolkit_BIN_DIR}" DIRECTORY)
        set(CUDAToolkit_TARGET_DIR "${CUDAToolkit_ROOT}")
        set(CUDAToolkit_LIBRARY_ROOT "${CUDAToolkit_ROOT}/lib")
    else()
        if(NOT CUDAToolkit_FIND_QUIETLY)
            message(WARNING "Found NVCC at ${CUDAToolkit_NVCC_EXECUTABLE},"
                            " but its version '${CMAKE_MATCH_1}' did not match cuda-driver-stubs version of '${CUDAToolkit_VERSION}'.")
        endif()
        set(CUDAToolkit_NVCC_EXECUTABLE "")
    endif()
endif()
