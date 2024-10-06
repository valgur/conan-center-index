#include <X11/Xlib.h>
#include <X11/extensions/xf86vmode.h>

#include <stddef.h>

void dummy() {
    XF86VidModeGetPermissions(NULL, 0, 0);
}

int main() {
}
