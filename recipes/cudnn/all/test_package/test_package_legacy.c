#include <cudnn_ops.h>
#include <stdio.h>

int main() {
    size_t version = cudnnGetVersion();
    int major = version / 10000;
    int minor = (version % 10000) / 100;
    int patch = version % 100;
    printf("cuDNN version: %d.%d.%d\n", major, minor, patch);

    cudnnStatus_t status = cudnnOpsVersionCheck();
    if (status != CUDNN_STATUS_SUCCESS) {
        printf("cuDNN Ops version check failed: %s\n", cudnnGetErrorString(status));
        return 1;
    }
}
