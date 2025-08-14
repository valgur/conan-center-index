#include <cuda/experimental/version.cuh>
#include <iostream>

int main() {
    std::cout << "CUDA Experimental API version: "
        << CUDAX_VERSION_MAJOR << "."
        << CUDAX_VERSION_MINOR << "."
        << CUDAX_VERSION_PATCH << std::endl;
}
