#include <X11/fonts/fontenc.h>

#include <stdio.h>

int main() {
    const char* directory = FontEncDirectory();
    printf("FontEncDirectory: %s\n", directory);
}
