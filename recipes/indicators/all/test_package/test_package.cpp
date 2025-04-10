// indicators/termcolor.hpp is missing #include <cstdint>
#include <cstdint>

#include <indicators/cursor_control.hpp>
#include <indicators/progress_bar.hpp>
#include <indicators/progress_spinner.hpp>

int main() {
  indicators::show_console_cursor(true);
}
