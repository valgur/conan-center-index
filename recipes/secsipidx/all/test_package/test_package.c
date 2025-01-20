#include <secsipid.h>

#include <stdio.h>

int main() {
    SecSIPIDOptSetN("CacheExpires", 1000);
    printf("Set CacheExpires to 1000");
}
