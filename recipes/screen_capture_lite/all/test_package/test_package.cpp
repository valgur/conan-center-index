#include "ScreenCapture.h"
#include <iostream>

int main() {
    SL::Screen_Capture::CreateCaptureConfiguration(
        []() { return SL::Screen_Capture::GetMonitors(); });
}
