#include <sanitizer.h>
#include <stddef.h>

int main() {
    sanitizerAlloc(NULL, NULL, 0);
}
