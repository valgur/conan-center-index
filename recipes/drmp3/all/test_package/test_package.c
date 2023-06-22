#include "dr_mp3.h"
#include <stdio.h>

int main(void) {
    const char *version = drmp3_version_string();
    printf("dr_mp3 version: %s\n", version);

    return 0;
}
