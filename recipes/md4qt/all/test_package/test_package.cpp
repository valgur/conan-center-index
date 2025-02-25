// include/md4qt/traits.hpp is missing an #include <utility> for std::as_const
#include <utility>

#define MD4QT_ICU_STL_SUPPORT
#ifdef MD4QT_VERSION_GREATER_EQUAL_4
#include <md4qt/parser.h>
#else
#include <md4qt/parser.hpp>
#endif

int main(int argc, char ** argv)
{
    MD::Parser< MD::UnicodeStringTrait > parser;
}
