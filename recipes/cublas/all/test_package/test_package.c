#include <cublas_v2.h>
#include <stdio.h>

int main() {
    cublasStatus_t status;
    cublasHandle_t handle;
    status = cublasCreate_v2(&handle);
    if (status != CUBLAS_STATUS_SUCCESS) {
        printf("cuBLAS API error: %d\n", status);
        return 0;
    }
    int version;
    status = cublasGetVersion(handle, &version);
    if (status != CUBLAS_STATUS_SUCCESS) {
        printf("cuBLAS API error: %d\n", status);
        return 0;
    }
    int major = version / 10000;
    int minor = version % 10000 / 100;
    int patch = version % 100;
    printf("cuBLAS version: %d.%d.%d\n", major, minor, patch);
}
