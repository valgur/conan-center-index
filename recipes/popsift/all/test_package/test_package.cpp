#include <popsift/popsift.h>

int main() {
    popsift::Config config;
    PopSift popsift(config, popsift::Config::ExtractingMode, PopSift::ByteImages);
}
