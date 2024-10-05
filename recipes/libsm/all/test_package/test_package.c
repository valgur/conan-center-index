#include <X11/SM/SMlib.h>

#include <stdlib.h>

int main() {
    SmProp *prop = malloc(sizeof(SmProp));
    SmFreeProperty(prop);
}
