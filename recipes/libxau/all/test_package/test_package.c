#include <X11/Xauth.h>

#include <stdio.h>

int main() {
    char* filename = XauFileName();
    printf("XauFileName: %s\n", filename);
}
