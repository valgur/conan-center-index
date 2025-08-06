#include <stddef.h>
#include <nv_decode.h>
#include <stdio.h>
#include <stdlib.h>

int main() {
    const char *mangled_name = "_ZN6Scope15Func1Enez";
    char *demangled_name = NULL;
    size_t length = 0;
    int status = 0;
    demangled_name = __cu_demangle(mangled_name, NULL, &length, &status);
    if (status == 0) {
        printf("Demangled %s: %s\n", mangled_name, demangled_name);
        free(demangled_name);
    } else {
        printf("Demangling failed with status: %d\n", status);
    }
}
