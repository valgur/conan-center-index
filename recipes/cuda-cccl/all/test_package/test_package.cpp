#include <cuda/std/version>
#include <iostream>

int main() {
    std::cout << "CCCL version: "
#ifdef CCCL_VERSION
        << CCCL_MAJOR_VERSION << "."
        << CCCL_MINOR_VERSION << "."
        << CCCL_PATCH_VERSION << std::endl;
#else
        << _LIBCUDACXX_CUDA_API_VERSION_MAJOR << "."
        << _LIBCUDACXX_CUDA_API_VERSION_MINOR << "."
        << _LIBCUDACXX_CUDA_API_VERSION_PATCH << std::endl;
#endif
}
