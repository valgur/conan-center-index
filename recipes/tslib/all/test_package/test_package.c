#include <tslib.h>

#include <stdio.h>


int main() {
    struct ts_lib_version_data *version = ts_libversion();
    printf("tslib version: %s\n", version->package_version);
}
