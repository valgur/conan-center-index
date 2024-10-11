#include <X11/Xlib.h>
#include <X11/extensions/XRes.h>

#include <stddef.h>

void dummy() {
    XResClientIdsDestroy(0, NULL);

}

int main() {
}
