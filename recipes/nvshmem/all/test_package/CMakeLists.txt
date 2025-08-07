cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CUDA CXX)

find_package(CUDAToolkit REQUIRED)
find_package(NVSHMEM REQUIRED)

add_executable(${PROJECT_NAME}_static test_package.cu)
target_link_libraries(${PROJECT_NAME}_static PRIVATE CUDA::cuda_driver CUDA::cudart nvshmem::nvshmem )
set_target_properties(${PROJECT_NAME}_static PROPERTIES CUDA_SEPARABLE_COMPILATION ON)

add_executable(${PROJECT_NAME}_shared test_package.cu)
target_link_libraries(${PROJECT_NAME}_shared PRIVATE CUDA::cuda_driver CUDA::cudart nvshmem::nvshmem_host nvshmem::nvshmem_device)
set_target_properties(${PROJECT_NAME}_shared PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
