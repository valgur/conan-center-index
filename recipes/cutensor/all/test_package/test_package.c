#include <cutensor.h>
#include <stdio.h>

int main() {
    size_t version = cutensorGetVersion();
    int major = version / 10000;
    int minor = (version / 100) % 100;
    int patch = version % 100;
    printf("cutensor version: %d.%d.%d\n", major, minor, patch);
}
