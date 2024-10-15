// include/md4qt/traits.hpp is missing an #include <utility> for std::as_const
#include <utility>

#define MD4QT_ICU_STL_SUPPORT
#include <md4qt/parser.hpp>

int main(int argc, char ** argv)
{
    MD::Parser< MD::UnicodeStringTrait > parser;
}
