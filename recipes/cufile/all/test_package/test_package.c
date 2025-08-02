#include <cufile.h>
#include <stdio.h>

int main() {
    int version;
    CUfileError_t error = cuFileGetVersion(&version);
    if (error.err != CU_FILE_SUCCESS) {
        printf("cuFile API error: %d\n", error.err);
        return 1;
    }
    int major = version / 1000;
    int minor = (version % 1000) / 10;
    int patch = version % 10;
    printf("cuFile version: %d.%d.%d\n", major, minor, patch);
}
