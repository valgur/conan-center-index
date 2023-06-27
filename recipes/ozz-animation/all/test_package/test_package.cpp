#include <iostream>

#include "ozz/base/io/stream.h"
#include "ozz/base/log.h"

int main() {
    ozz::io::File file("test.ozz", "rb");

    if (!file.opened()) {
    }
}
