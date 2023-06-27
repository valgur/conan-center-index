#include <pulse/pulseaudio.h>
#include <stdio.h>

int main() {
    printf("pulse audio verions %s\n", pa_get_library_version());
    return 0;
}
