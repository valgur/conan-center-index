#include <cuda_runtime.h>
#include <stdio.h>

int main() {
    int version;
    cudaError_t error = cudaRuntimeGetVersion(&version);
    if (error != cudaSuccess) {
        printf("CUDA Runtime API error: %s\n", cudaGetErrorString(error));
        return 0;
    }
    int major = version / 1000;
    int minor = version % 1000 / 10;
    int patch = version % 10;
    printf("CUDA Runtime version: %d.%d.%d\n", major, minor, patch);
}
