#include <cudnn_frontend.h>

int main() {
    printf("cuDNN FE version: %d.%d.%d\n",
        CUDNN_FRONTEND_MAJOR_VERSION,
        CUDNN_FRONTEND_MINOR_VERSION,
        CUDNN_FRONTEND_PATCH_VERSION
    );
}
