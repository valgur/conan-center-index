find_package(asmjit REQUIRED CONFIG)
find_package(cpuinfo REQUIRED CONFIG)
find_package(fbgemmLibrary REQUIRED CONFIG)
link_libraries(asmjit::asmjit cpuinfo::cpuinfo fbgemm)
