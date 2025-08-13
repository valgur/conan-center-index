#include <nvcomp.hpp>
#include <nvcomp/zstd.hpp>
#include <stdio.h>

int main() {
    nvcompProperties_t props;
    nvcompStatus_t status = nvcompGetProperties(&props);
    if (status != nvcompSuccess) {
        printf("Failed to get nvcomp properties: %d\n", status);
        return -1;
    }
    int major = props.version / 1000;
    int minor = (props.version % 1000) / 100;
    int patch = props.version % 100;
    printf("nvCOMP version: %d.%d.%d\n", major, minor, patch);
}
