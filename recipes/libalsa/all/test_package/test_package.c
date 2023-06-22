#include <alsa/global.h>
#include <stdio.h>

int main() {
    printf("libalsa version %s\n", snd_asoundlib_version());
    return 0;
}
