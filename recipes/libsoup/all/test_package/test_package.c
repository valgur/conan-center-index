#include <libsoup/soup.h>
#include <stdio.h>

int main() {
    int major_version = soup_get_major_version();
    int minor_version = soup_get_minor_version();
    int micro_version = soup_get_micro_version();
    printf("libsoup version: %d.%d.%d\n", major_version, minor_version, micro_version);
}
