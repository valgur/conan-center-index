#include <xercesc/util/PlatformUtils.hpp>

int main() {
    try {
        xercesc::XMLPlatformUtils::Initialize();
    } catch (const xercesc::XMLException &toCatch) {
        return 1;
    }

    xercesc::XMLPlatformUtils::Terminate();

    return 0;
}
