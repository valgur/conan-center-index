#include <cupti.h>
#include <nvperf_host.h>
#include <nvperf_target.h>
#include <cupti_pcsampling_util.h>
#include <cupti_checkpoint.h>
#include <stdio.h>

int main() {
    uint32_t version;
    CUptiResult status = cuptiGetVersion(&version);
    if (status != CUPTI_SUCCESS) {
        printf("CUPTI API error: %d\n", status);
        return 1;
    }
    printf("CUPTI API version: %d\n", version);
}
