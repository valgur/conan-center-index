#include <gdrapi.h>
#include <stdio.h>

int main() {
    int major, minor;
    gdr_runtime_get_version(&major, &minor);
    printf("GDRCopy version: %d.%d\n", major, minor);
}
