#include <cusparseLt.h>
#include <stdio.h>

int main() {
    int major, minor, patch;
    int status = CUSPARSE_STATUS_SUCCESS;
    status |= cusparseLtGetProperty(MAJOR_VERSION, &major);
    status |= cusparseLtGetProperty(MINOR_VERSION, &minor);
    status |= cusparseLtGetProperty(PATCH_LEVEL, &patch);
    if (status != CUSPARSE_STATUS_SUCCESS) {
        printf("cuSPARSELt API error: %d\n", status);
        return 1;
    }
    printf("cuSPARSELt version: %d.%d.%d\n", major, minor, patch);
}
