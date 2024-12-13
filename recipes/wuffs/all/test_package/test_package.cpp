#include <wuffs-v0.3.c>

int main() {
    wuffs_aux::MemOwner mem_owner(nullptr, &free);
}
