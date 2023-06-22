#include <PcapPlusPlusVersion.h>
#include <cstdlib>
#include <iostream>

int main() {
    std::cout << "PCAP++ VERSION: " << pcpp::getPcapPlusPlusVersionFull() << std::endl;
    return EXIT_SUCCESS;
}
