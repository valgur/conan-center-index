#include <X11/extensions/Xfixes.h>

#include <stddef.h>

void dummy() {
    XFixesGetCursorName(NULL, NULL, NULL);
}

int main() {
}
