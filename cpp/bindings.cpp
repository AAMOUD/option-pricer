#include <pybind11/pybind11.h>
#include "pricer.hpp"

namespace py = pybind11;

PYBIND11_MODULE(pricer_cpp, m) {
    m.doc() = "C++ option pricing engine";

    m.def("binomial_price", &binomial_price_cpp,
          py::arg("spot"), py::arg("strike"), py::arg("rate"),
          py::arg("vol"), py::arg("maturity"), py::arg("is_call"),
          py::arg("is_american"), py::arg("steps"));

    m.def("heston_price", &heston_price_cpp,
          py::arg("spot"), py::arg("strike"), py::arg("rate"),
          py::arg("vol"), py::arg("maturity"), py::arg("is_call"),
          py::arg("num_sims"), py::arg("kappa"), py::arg("sigma"),
          py::arg("rho"));
}
