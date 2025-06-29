#include <ultrahdr_api.h>
#include <iostream>

int main()
{
    uhdr_codec_private_t* decoder = uhdr_create_decoder();
    uhdr_release_decoder(decoder);
    std::cout << "libUltraHDR library version: " << UHDR_LIB_VERSION_STR << "\n";
}
