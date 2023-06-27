#ifdef TRACY_GE_0_9
#include <tracy/Tracy.hpp>
#else
#include <Tracy.hpp>
#endif

int main() {
    ZoneScopedN("main");

    return 0;
}
