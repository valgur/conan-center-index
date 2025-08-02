#include <cusolverDn.h>
#include <cusolverMg.h>
#include <cusolverRf.h>
#include <cusolverSp.h>
#include <stdio.h>

int main() {
    int version;
    cusolverStatus_t status = cusolverGetVersion(&version);
    if (status != CUSOLVER_STATUS_SUCCESS) {
        printf("cuSOLVER API error: %d\n", status);
        return 1;
    }
    int major = version / 1000;
    int minor = (version % 1000) / 100;
    int patch = version % 100;
    printf("cuSOLVER version: %d.%d.%d\n", major, minor, patch);
}
