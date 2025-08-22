#include <cudensitymat.h>
#include <custatevec.h>
#include <cutensornet.h>
#include <stdio.h>

void print_version(char* name, size_t version) {
    int major = version / 10000;
    int minor = (version % 10000) / 100;
    int patch = version % 100;
    printf("%s version: %d.%d.%d\n", name, major, minor, patch);
}

int main() {
    print_version("cudensitymat", cudensitymatGetVersion());
    print_version("custatevec", custatevecGetVersion());
    print_version("cutensornet", cutensornetGetVersion());
}
