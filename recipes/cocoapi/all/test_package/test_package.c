#include <maskApi.h>
#include <stdio.h>

int main() {
    uint cnts[] = { 3, 4, 1 };
    RLE rle = { 3, 4, 1, cnts };
    char *s = rleToString( &rle );
    printf("%s\n", s);
    free(s);
}
