#include <cufftw.h>
#include <stdio.h>

int main() {
    int version;
    cufftResult status = cufftGetVersion(&version);
    if (status != CUFFT_SUCCESS) {
        printf("cuFFT API error: %d\n", status);
        return 1;
    }
    int major = version / 1000;
    int minor = (version % 1000) / 100;
    int patch = version % 100;
    printf("cuFFT version: %d.%d.%d\n", major, minor, patch);
}
