#include <leptonica/allheaders.h>
#include <stdio.h>

int main() {
    printf("Leptonica version: %d.%d.%d\n", LIBLEPT_MAJOR_VERSION, LIBLEPT_MINOR_VERSION,
           LIBLEPT_PATCH_VERSION);
    printf("Lib versions: %s\n", getImagelibVersions());
    return 0;
}
