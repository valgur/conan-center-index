#include <rasterlite.h>
#include <sqlite3.h>

#include <stdio.h>

int main(void) {
    printf("rasterlite %s\n", rasterliteGetVersion());
    return 0;
}
