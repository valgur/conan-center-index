#include <X11/extensions/Xcomposite.h>

#include <stdio.h>

int main() {
    printf("XCompositeVersion: %d\n", XCompositeVersion());
}
