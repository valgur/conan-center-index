#include "CglProbing.hpp"

int main() {
    CglProbing probing;
    probing.setLogLevel(0);
    probing.setUsingObjective(1);
    return probing.getUsingObjective() == 1 ? 0 : 1;
}
