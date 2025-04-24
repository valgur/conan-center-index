#if QT_MAJOR == 6
    #include "qt6keychain/keychain.h"
#else
    #include "qt5keychain/keychain.h"
#endif

int main()
{
    QKeychain::isAvailable();
}
