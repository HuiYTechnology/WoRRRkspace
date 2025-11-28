cmake_minimum_required(VERSION 3.15)
project(RrrrProject LANGUAGES CXX)

# Настройки для MSVC и C++20
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Настройки для MSVC
if(MSVC)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
    add_compile_options("$<$<C_COMPILER_ID:MSVC>:/utf-8>")
    add_compile_options("$<$<CXX_COMPILER_ID:MSVC>:/utf-8>")

    # Отключаем некоторые предупреждения MSVC
    add_compile_options("/W4")
    add_compile_options("/wd4100") # unreferenced formal parameter
    add_compile_options("/wd4201") # nonstandard extension used: nameless struct/union
    add_compile_options("/wd4458") # declaration hides class member
    add_compile_options("/wd4996") # unsafe functions (например, strcpy)
endif()

# Политики для совместимости
if(POLICY CMP0068)
    cmake_policy(SET CMP0068 NEW)
endif()

# Включение C++ утилит (обновленный путь)
add_subdirectory(src/cpp)

# Для Windows специфичные настройки
if(WIN32)
    # Дополнительные определения для Windows
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)

    # Настройки для статической линковки runtime библиотек
    if(MSVC)
        set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    endif()
endif()

# Создание папки для логов
add_custom_target(create_logs_dir ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_SOURCE_DIR}/logs
    COMMENT "Creating logs directory"
)

# Информация о проекте
message(STATUS "Project: ${PROJECT_NAME}")
message(STATUS "C++ Compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Source directory: ${CMAKE_SOURCE_DIR}")
message(STATUS "Binary directory: ${CMAKE_BINARY_DIR}")