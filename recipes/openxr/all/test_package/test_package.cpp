#include <openxr/openxr.h>

#include <cstdlib>


int main() {
    XrApplicationInfo app_info = {};
#ifdef HAVE_OPENXR_LOADER
    uint32_t ext_count = 0;
	xrEnumerateInstanceExtensionProperties(nullptr, 0, &ext_count, nullptr);
#endif
}
