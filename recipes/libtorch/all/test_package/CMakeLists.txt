cmake_minimum_required(VERSION 3.15)
project(test_package CXX CUDA)

find_package(Torch REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} torch)
target_compile_features(test_package PRIVATE cxx_std_17)
set_target_properties(${PROJECT_NAME} PROPERTIES CUDA_RESOLVE_DEVICE_SYMBOLS ON)

# Workaround for
# CompositeViewCopyKernels.cpp:(.text+0x1a280): failed to convert GOTPCREL relocation against '_ZN3c1019UndefinedTensorImpl10_singletonE'; relink with --no-relax
# etc.
include(CheckLinkerFlag)
if(UNIX AND NOT APPLE)
  check_linker_flag(CXX "-Wl,--no-relax" LD_NO_RELAX_SUPPORTED)
  target_link_options(test_package PRIVATE -Wl,--no-relax)
endif()

# Not quite sure why, but explicitly linking against nccl::nccl fixes a deluge of these linker errors when building as static:
# nccleb76362a00ece/p/lib/libnccl_static.a(onerank.cu.o):(.text): relocation R_X86_64_PLT32 against TLS init function for ncclDebugNoWarn out of range: -2190985986 is not in [-2147483648, 2147483648)
find_package(nccl)
if(nccl_FOUND)
  target_link_libraries(${PROJECT_NAME} nccl::nccl)
endif()
