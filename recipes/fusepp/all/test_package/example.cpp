#include "Fuse-impl.h"
#include "Fuse.h"

class MyFilesystem : public Fusepp::Fuse<MyFilesystem> {};

int main() { MyFilesystem(); }
