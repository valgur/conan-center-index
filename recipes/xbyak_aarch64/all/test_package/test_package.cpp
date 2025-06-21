#include <xbyak_aarch64/xbyak_aarch64.h>
#include <xbyak_aarch64/xbyak_aarch64_util.h>

int main() {
    Xbyak_aarch64::util::Cpu cpu;
    cpu.dumpCacheInfo();
}
