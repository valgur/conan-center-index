#include <X11/Xdmcp.h>

int main() {
    XdmAuthKeyRec key;
    XdmcpGenerateKey(&key);
}
