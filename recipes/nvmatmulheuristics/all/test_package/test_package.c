#include <nvMatmulHeuristics.h>
#include <stdio.h>

int main() {
    char buffer[256];
    nvMatmulHeuristicsGetVersionString(buffer, sizeof(buffer));
    printf("nvMatmulHeuristics version: %s\n", buffer);
}
