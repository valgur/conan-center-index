find_package(gumbo-parser REQUIRED CONFIG)
add_library(gumbo ALIAS gumbo-parser::gumbo-parser)
