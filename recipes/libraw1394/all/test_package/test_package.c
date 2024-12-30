#include <libraw1394/raw1394.h>
#include <stdio.h>

int main()
{
    const char* libraw1394_version = raw1394_get_libversion();
    printf("libraw1394 version: %s\n", libraw1394_version);
}
