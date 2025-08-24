#include <cstdint>
#include <cvcuda/OpCustomCrop.hpp>
#include <cvcuda/OpResize.hpp>
#include <cvcuda/OpFindHomography.hpp>

int main() {
    cvcuda::CustomCrop cropOp;
    cvcuda::Resize resizeOp;
    cvcuda::FindHomography homographyOp{1, 1};
}
