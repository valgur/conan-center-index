#include <nvcomp.hpp>
#include <nvcomp/zstd.hpp>
#include <stdio.h>

int main() {
    nvcomp::ZstdManager zstd_manager{1024, nvcompBatchedZstdOpts_t{}};
    printf("nvCOMP version: %d.%d.%d.%d\n", NVCOMP_VER_MAJOR, NVCOMP_VER_MINOR, NVCOMP_VER_PATCH, NVCOMP_VER_BUILD);
}
