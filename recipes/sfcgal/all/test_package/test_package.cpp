// Based on https://gitlab.com/sfcgal/SFCGAL/-/blob/v1.5.0/example/CGAL-basic_manip/main.cpp

/**
 *   SFCGAL
 *
 *   Copyright (C) 2012-2013 Oslandia <infos@oslandia.com>
 *   Copyright (C) 2012-2013 IGN (http://www.ign.fr)
 *
 *   This library is free software; you can redistribute it and/or
 *   modify it under the terms of the GNU Library General Public
 *   License as published by the Free Software Foundation; either
 *   version 2 of the License, or (at your option) any later version.
 *
 *   This library is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *   Library General Public License for more details.

 *   You should have received a copy of the GNU Library General Public
 *   License along with this library; if not, see <http://www.gnu.org/licenses/>.
 */
#include <iostream>

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/Point_3.h>
#include <CGAL/Triangle_3.h>

/**
 * Defines the default Kernel used by SFCGAL
 */
typedef CGAL::Exact_predicates_exact_constructions_kernel Kernel ;

typedef Kernel::Point_3           Point_3 ;
typedef Kernel::Triangle_3        Triangle_3 ;


int main(){
	std::cout << "--- Triangle_3 ---" << std::endl;
    Triangle_3 tri( Point_3( 0.0, 0.0, 1.0),
            Point_3( 1.0, 0.0, 1.0),
            Point_3( 0.0, 1.0, 1.0) );
    Point_3 p( 0.2, 0.2, 1.0 );
    Point_3 p2( 0.2, 0.2, 0.0 );
    std::cout << "p  : " << p << std::endl;
    std::cout << "p2 : " << p2 << std::endl;
    std::cout << "tri: " << tri << std::endl;
    std::cout << "tri.has_on(p) : " << tri.has_on( p ) << std::endl;
    std::cout << "tri.has_on(p2): " << tri.has_on( p2 ) << std::endl;
	return 0;
}
