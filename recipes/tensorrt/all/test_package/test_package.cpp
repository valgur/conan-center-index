#include <NvInfer.h>
#include <cstdio>

int main() {
    int32_t version = getInferLibVersion();
#if NV_TENSORRT_VERSION >= 10000
    int major = version / 10000;
    int minor = (version % 10000) / 100;
    int patch = version % 100;
#else
    int major = version / 1000;
    int minor = (version % 1000) / 100;
    int patch = version % 100;
#endif
    printf("TensorRT version: %d.%d.%d\n", major, minor, patch);
}
