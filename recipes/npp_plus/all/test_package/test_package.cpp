#define NPP_PLUS_ENABLE
#include <nppPlus/nppPlus.h>
#include <nppPlus/nppiPlus_filtering_functions.h>
#include <stdio.h>

int main() {
    const NppLibraryVersion *libVer = nppPlusV::nppGetLibVersion();
    printf("NPP Library Version %d.%d.%d\n", libVer->major, libVer->minor, libVer->build);

    size_t bufferSize;
    nppPlusV::nppiDistanceTransformPBAGetBufferSize(NppiSize{100, 100}, &bufferSize);
}
