#include "gpiod.h"

int main() {
    struct gpiod_chip *chip;
    chip = gpiod_chip_open_by_name("gpiochip0");
    return 0;
}
