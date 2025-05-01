#include <cups/cups.h>

#include <stdio.h>

int main() {
    printf("CUPS user agent: %s\n", cupsUserAgent());
}
