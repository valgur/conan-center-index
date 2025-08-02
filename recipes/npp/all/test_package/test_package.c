#include <npp.h>
#include <stdio.h>

int main() {
    const NppLibraryVersion *version = nppGetLibVersion();
    if (version == NULL) {
        printf("Failed to get NPP library version.\n");
        return 1;
    }
    printf("NPP version: %d.%d.%d\n", version->major, version->minor, version->build);
}
