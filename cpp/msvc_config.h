#pragma once

// MSVC
#ifdef _MSC_VER
    #pragma warning(disable : 4100) // unreferenced formal parameter
    #pragma warning(disable : 4201) // nonstandard extension used: nameless struct/union
    #pragma warning(disable : 4458) // declaration hides class member
    #pragma warning(disable : 4996) // unsafe functions

    // C++20
    #define _HAS_CXX20 1

    #define _USE_MATH_DEFINES

    #ifndef M_PI
        #define M_PI 3.14159265358979323846
    #endif

    #define _SCL_SECURE_NO_WARNINGS
    #define _CRT_SECURE_NO_WARNINGS
#endif