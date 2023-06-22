#include <tesseract/baseapi.h>

#include <stdio.h>

int main() {
    printf("Tesseract version: %s\n", tesseract::TessBaseAPI::Version());
    return 0;
}
