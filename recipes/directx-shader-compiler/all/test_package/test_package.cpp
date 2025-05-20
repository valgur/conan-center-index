#include <dxc/dxcapi.h>

int main() {
    IDxcLibrary* pLibrary;
    IDxcCompiler* pCompiler;
    DxcCreateInstance(CLSID_DxcLibrary, IID_PPV_ARGS(&pLibrary));
    DxcCreateInstance(CLSID_DxcCompiler, IID_PPV_ARGS(&pCompiler));
    pLibrary->Release();
    pCompiler->Release();
}
