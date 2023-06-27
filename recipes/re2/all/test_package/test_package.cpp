#include <re2/re2.h>

#include <cassert>
#include <iostream>

int main() {
    assert(RE2::FullMatch("hello", "h.*o"));
    assert(!RE2::FullMatch("hello", "e"));
    return 0;
}
