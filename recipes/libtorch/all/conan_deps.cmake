# A wrapper for https://github.com/pytorch/pytorch/blob/v2.4.0/cmake/Dependencies.cmake

# Moved initialization of these vars here so they can be overridden
set(ATen_CPU_DEPENDENCY_LIBS)
set(ATen_XPU_DEPENDENCY_LIBS)
set(ATen_CUDA_DEPENDENCY_LIBS)
set(ATen_HIP_DEPENDENCY_LIBS)
set(ATen_PUBLIC_CUDA_DEPENDENCY_LIBS)
set(ATen_PUBLIC_HIP_DEPENDENCY_LIBS)
set(Caffe2_DEPENDENCY_LIBS)
set(Caffe2_CUDA_DEPENDENCY_LIBS)

find_package(concurrentqueue REQUIRED CONFIG)
find_package(cpuinfo REQUIRED CONFIG)
find_package(fmt REQUIRED CONFIG)
find_package(httplib REQUIRED CONFIG)
find_package(miniz REQUIRED CONFIG)
find_package(nlohmann_json REQUIRED CONFIG)
find_package(ONNX REQUIRED CONFIG)
find_package(pocketfft REQUIRED CONFIG)

list(APPEND Caffe2_DEPENDENCY_LIBS
    cpuinfo
    fmt::fmt-header-only
    httplib::httplib
    miniz::miniz
    moodycamel
    nlohmann
    onnx::onnx
    pocketfft::pocketfft
)

if(USE_KINETO)
    find_package(kinetoLibrary REQUIRED)
    list(APPEND Caffe2_DEPENDENCY_LIBS kineto)
endif()

if(CONAN_LIBTORCH_USE_FLATBUFFERS)
    find_package(flatbuffers REQUIRED CONFIG)
    list(APPEND Caffe2_DEPENDENCY_LIBS flatbuffers::flatbuffers)
endif()

if(CONAN_LIBTORCH_USE_SLEEF)
    find_package(sleef REQUIRED CONFIG)
    list(APPEND ATen_CPU_DEPENDENCY_LIBS sleef::sleef)
    list(APPEND Caffe2_DEPENDENCY_LIBS sleef::sleef)
endif()

if(USE_GFLAGS)
    find_package(gflags REQUIRED CONFIG)
    list(APPEND Caffe2_DEPENDENCY_LIBS gflags)
    list(APPEND Caffe2_CUDA_DEPENDENCY_LIBS gflags)
    list(APPEND ATen_CUDA_DEPENDENCY_LIBS gflags)
endif()

if(USE_GLOG)
    find_package(glog REQUIRED CONFIG)
    list(APPEND Caffe2_DEPENDENCY_LIBS glog::glog)
    list(APPEND Caffe2_CUDA_DEPENDENCY_LIBS glog::glog)
    list(APPEND ATen_CUDA_DEPENDENCY_LIBS glog::glog)
endif()

if(USE_XNNPACK)
    find_package(xnnpack REQUIRED CONFIG)
    list(APPEND Caffe2_DEPENDENCY_LIBS xnnpack::xnnpack)
    add_library(XNNPACK INTERFACE)
endif()

if(USE_FBGEMM)
    find_package(fbgemmLibrary REQUIRED CONFIG)
    list(APPEND Caffe2_DEPENDENCY_LIBS fbgemm)
endif()

if(USE_NNPACK)
    find_package(nnpack REQUIRED CONFIG)
endif()

if(USE_PYTORCH_QNNPACK)
    find_package(fp16 REQUIRED CONFIG)
    find_package(fxdiv REQUIRED CONFIG)
    find_package(psimd REQUIRED CONFIG)
    find_package(pthreadpool REQUIRED CONFIG)
    list(APPEND Caffe2_DEPENDENCY_LIBS pthreadpool::pthreadpool)
    add_library(pthreadpool ALIAS pthreadpool::pthreadpool)
else()
    # Add a dummy fp16 target to disable a check in Dependencies.cmake
    add_library(fp16 INTERFACE)
endif()

if(USE_MIMALLOC)
    find_package(mimalloc REQUIRED CONFIG)
endif()

if(USE_CUDNN)
    find_package(cudnn_frontend REQUIRED CONFIG)
endif()

if(USE_TENSORPIPE)
    find_package(Tensorpipe REQUIRED CONFIG)
endif()

if(USE_CUDA)
    find_package(NvidiaCutlass REQUIRED)
    list(APPEND Caffe2_CUDA_DEPENDENCY_LIBS nvidia::cutlass::cutlass)
endif()
if(USE_GLOO)
    find_package(Gloo REQUIRED)
    list(APPEND Caffe2_CUDA_DEPENDENCY_LIBS gloo::gloo)
endif()
