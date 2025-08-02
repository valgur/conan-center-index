#include <cusparse_v2.h>
#include <stdio.h>

int main() {
    cusparseStatus_t status = CUSPARSE_STATUS_SUCCESS;
    int major, minor, patch;
    status |= cusparseGetProperty(MAJOR_VERSION, &major);
    status |= cusparseGetProperty(MINOR_VERSION, &minor);
    status |= cusparseGetProperty(PATCH_LEVEL, &patch);
    if (status != CUSPARSE_STATUS_SUCCESS) {
        printf("cuSPARSE API error: %d\n", status);
        return 1;
    }
    printf("cuSPARSE version: %d.%d.%d\n", major, minor, patch);
}
