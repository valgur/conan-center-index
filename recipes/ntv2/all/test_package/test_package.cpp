#include <ntv2card.h>
#include <ntv2utils.h>

int main() {
    std::cout << "hello AJA NTV2 version " << NTV2GetVersionString() << "\n";
    CNTV2Card card;
    std::cout << "card name is " << card.GetDisplayName() << '\n';
    return 0;
}
