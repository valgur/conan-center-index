find_package(CUDAToolkit REQUIRED)

set_property(TARGET gtsam_points::gtsam_points_cuda PROPERTY INTERFACE_LINK_LIBRARIES CUDA::cudart APPEND)
set_property(TARGET gtsam_points::gtsam_points_cuda PROPERTY INTERFACE_COMPILE_FEATURES cuda_std_17)
