find_package(OpenCLHeaders REQUIRED)
find_package(half REQUIRED)
find_package(libnpy REQUIRED)
find_package(stb REQUIRED)
set(ARM_COMPUTE_LINK_LIBS
    OpenCL::Headers
    half::half
    libnpy::libnpy
    stb::stb
)
