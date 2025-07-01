#include <dpi.h>
#include <iostream>

int main() {
    dpiVersionInfo versionInfo;
    dpiContext_getClientVersion(NULL, &versionInfo);
    std::cout << "ODPI Test Package executed with success." << std::endl;
}
