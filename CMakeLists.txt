cmake_minimum_required(VERSION 3.14)
project(option_pricer)

find_package(pybind11 REQUIRED)
pybind11_add_module(pricer_cpp cpp/pricer.cpp cpp/bindings.cpp)
target_compile_options(pricer_cpp PRIVATE -O3 -march=native)
