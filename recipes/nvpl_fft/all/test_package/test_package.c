#include <nvpl_fftw.h>
#include <stdio.h>

int main() {
    int version = nvpl_fft_get_version();
    int major = version / 10000;
    int minor = (version % 10000) / 100;
    int patch = version % 100;
    printf("nvpl_fft version: %d.%d.%d\n", major, minor, patch);
}
