// deco is missing an #include <cstdint>
#include <cstdint>

#include <deco/Deco.h>

#include <iostream>
#include <string>

int main()
{
	const std::string sample{
		"hello:\n"
		"	world!\n"
		":\n"
	};

	deco::parse(sample.begin(), sample.end());

	std::cout << sample << std::endl;
}
