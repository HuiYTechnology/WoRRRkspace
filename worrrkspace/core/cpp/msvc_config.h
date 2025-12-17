// msvc_config.h
#pragma once

// Конфигурация для MSVC компилятора
#ifdef _MSC_VER
    // Отключаем предупреждения для MSVC
    #pragma warning(disable : 4100) // unreferenced formal parameter
    #pragma warning(disable : 4201) // nonstandard extension used: nameless struct/union
    #pragma warning(disable : 4458) // declaration hides class member
    #pragma warning(disable : 4996) // unsafe functions

    // Гарантируем совместимость с C++20
    #define _HAS_CXX20 1

    // Для совместимости с математическими константами
    #define _USE_MATH_DEFINES

    // Для совместимости с M_PI и другими математическими константами
    #ifndef M_PI
        #define M_PI 3.14159265358979323846
    #endif

    // Для подавления предупреждений о безопасности
    #define _SCL_SECURE_NO_WARNINGS
    #define _CRT_SECURE_NO_WARNINGS
#endif