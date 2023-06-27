#include <nvtx3/nvToolsExt.h>
#include <stdlib.h>

int main() {
    nvtxInitialize(NULL);
    nvtxRangeId_t main_range = nvtxRangeStartA("main");
    nvtxRangeEnd(main_range);
    return EXIT_SUCCESS;
}
