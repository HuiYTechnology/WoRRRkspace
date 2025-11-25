cmake_minimum_required(VERSION 3.15)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(logger SHARED logger.cpp logger.h)
add_library(calculate SHARED calculate.cpp calculate.h)

target_link_libraries(calculate PRIVATE logger)

if(MSVC)
    target_compile_options(logger PRIVATE "/W4")
    target_compile_options(calculate PRIVATE "/W4")

    target_compile_options(logger PRIVATE "/wd4100" "/wd4201" "/wd4458" "/wd4996")
    target_compile_options(calculate PRIVATE "/wd4100" "/wd4201" "/wd4458" "/wd4996")

    set_property(TARGET logger PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    set_property(TARGET calculate PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

set_target_properties(logger calculate PROPERTIES
    OUTPUT_NAME ""
    PREFIX ""
)

if(WIN32)
    target_compile_definitions(logger PRIVATE _CRT_SECURE_NO_WARNINGS)
    target_compile_definitions(calculate PRIVATE _CRT_SECURE_NO_WARNINGS)
    set_target_properties(logger calculate PROPERTIES SUFFIX ".dll")

    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        set_target_properties(logger calculate PROPERTIES
            LINK_FLAGS "-static -static-libgcc -static-libstdc++"
        )
    endif()
else()
    set_target_properties(logger calculate PROPERTIES SUFFIX ".so")
endif()

set_target_properties(logger PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/cpp_logger/lib
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/cpp_logger/lib
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/cpp_logger/lib
)

set_target_properties(calculate PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/cpp_calculate/lib
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/cpp_calculate/lib
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/cpp_calculate/lib
)

install(
    TARGETS logger
    RUNTIME DESTINATION src/cpp_logger/lib
    LIBRARY DESTINATION src/cpp_logger/lib
    ARCHIVE DESTINATION src/cpp_logger/lib
)

install(
    TARGETS calculate
    RUNTIME DESTINATION src/cpp_calculate/lib
    LIBRARY DESTINATION src/cpp_calculate/lib
    ARCHIVE DESTINATION src/cpp_calculate/lib
)

message(STATUS "Building logger library")
message(STATUS "Building calculate library")