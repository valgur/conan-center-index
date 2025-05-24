#include <stk/Stk.h>
#include <stk/Mandolin.h>

#include <cstdlib>
#include <string>

int main() {
    std::string rawwaves_path = std::getenv("STK_RAWWAVE_PATH");
    if (!rawwaves_path.empty()) {
        stk::Stk::setRawwavePath(rawwaves_path);
    }

    stk::Mandolin mandolin(100);
}
