#pragma once

double binomial_price_cpp(double spot, double strike, double rate,
                           double vol, double maturity, bool is_call,
                           bool is_american, int steps);

double heston_price_cpp(double spot, double strike, double rate,
                         double vol, double maturity, bool is_call,
                         int num_sims, double kappa, double sigma,
                         double rho);
