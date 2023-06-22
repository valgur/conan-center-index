#include <Color.hpp>
#include <cstdlib>

int main() {
    Gfx::Color someColor;
    someColor.SetRed(176);

    return someColor.GetRed() == 176 ? EXIT_SUCCESS : EXIT_FAILURE;
}
