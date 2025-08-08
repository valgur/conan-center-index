#include <nvpl_tensor.h>
#include <stdio.h>

int main() {
    size_t version = nvpltensorGetVersion();
    int major = version / 10000;
    int minor = version % 10000 / 100;
    int patch = version % 100;
    printf("nvpl_tensor version: %d.%d.%d\n", major, minor, patch);
}
