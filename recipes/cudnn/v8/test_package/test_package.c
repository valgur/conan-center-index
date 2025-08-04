#include <cudnn.h>
#include <stdio.h>

int main() {
    size_t version = cudnnGetVersion();
    int major = version / 1000;
    int minor = (version % 1000) / 100;
    int patch = version % 100;
    printf("cuDNN version: %d.%d.%d\n", major, minor, patch);
}
