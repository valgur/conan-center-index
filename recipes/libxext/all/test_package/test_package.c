#include <X11/Xlib.h>
#include <X11/extensions/Xext.h>

int xext_error_handler(Display *,  _Xconst char*, _Xconst char*) {
    return 0;
}

int main() {
    XSetExtensionErrorHandler(xext_error_handler);
}
