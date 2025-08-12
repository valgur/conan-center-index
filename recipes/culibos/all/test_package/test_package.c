#include <stdint.h>
#include <stdio.h>

// culibos does not export a header file, so just declare one trivial symbol for testing purposes.
uint32_t culibosKernelIs64Bit(void);


int main() {
    printf("culibosKernelIs64Bit(): %u\n", culibosKernelIs64Bit());
}
