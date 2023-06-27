#include <pciaccess.h>
#include <stdlib.h>

int main(void) {
    pci_system_init();
    pci_system_cleanup();
    return EXIT_SUCCESS;
}
