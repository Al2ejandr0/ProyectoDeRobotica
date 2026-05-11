cmake_minimum_required(VERSION 4.2)
project(hero_ui)
set(CMAKE_CXX_STANDARD 20)

find_package(SDL3 REQUIRED)
find_package(OpenGL REQUIRED)

add_executable(hero_ui
        ui.cpp
)
target_link_libraries(hero_ui PRIVATE
        SDL3::SDL3
        OpenGL::OpenGL
)
add_custom_command(
    TARGET hero_ui
    POST_BUILD
    COMMAND ${CMAKE_COMMAND}
    ARGS -E copy $<TARGET_FILE:hero_ui> ${CMAKE_SOURCE_DIR}/..
)