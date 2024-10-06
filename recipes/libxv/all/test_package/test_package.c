#include <X11/Xlib.h>
#include <X11/extensions/Xvlib.h>

#include <stddef.h>

void dummy() {
    XvFreeEncodingInfo(NULL);
}

int main() {
}
