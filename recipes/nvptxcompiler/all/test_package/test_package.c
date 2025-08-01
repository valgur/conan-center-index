#include <nvPTXCompiler.h>
#include <stdio.h>

int main() {
    unsigned int major, minor;
    nvPTXCompileResult result = nvPTXCompilerGetVersion(&major, &minor);
    if (result != NVPTXCOMPILE_SUCCESS) {
        fprintf(stderr, "Failed to get nvPTX compiler version\n");
        return 1;
    }
    printf("nvPTX Compiler version: %u.%u\n", major, minor);
}
