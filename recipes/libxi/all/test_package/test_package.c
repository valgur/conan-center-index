#include <X11/extensions/XInput2.h>

#include <stdlib.h>

int main() {
    XIDeviceInfo* device_info = malloc(sizeof(XIDeviceInfo));
    XIFreeDeviceInfo(device_info);
}
