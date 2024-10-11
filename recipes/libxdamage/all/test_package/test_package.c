#include <X11/extensions/Xdamage.h>

#include <stddef.h>

void dummy() {
    XDamageCreate(NULL, NULL, 0);
}

int main() {
}
