#include <nvcuvid.h>
#include <nvEncodeAPI.h>
#include <stdio.h>

int dummy_main() {
    uint32_t max_version;
    NVENCSTATUS status = NvEncodeAPIGetMaxSupportedVersion(&max_version);
    if (status != NV_ENC_SUCCESS) {
        fprintf(stderr, "Failed to get max supported version: %d\n", status);
        return 1;
    }
    int major = max_version >> 4;
    int minor = max_version & 0xFF;
    printf("NVENC API max supported version: %d.%d\n", major, minor);
}

int main() {
}
