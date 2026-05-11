#include "pricer.hpp"
#include <cmath>
#include <vector>
#include <algorithm>
#include <random>

double binomial_price_cpp(double spot, double strike, double rate,
                           double vol, double maturity, bool is_call,
                           bool is_american, int steps) {
    double dt   = maturity / steps;
    double u    = std::exp(vol * std::sqrt(dt));
    double d    = 1.0 / u;
    double p    = (std::exp(rate * dt) - d) / (u - d);
    double disc = std::exp(-rate * dt);

    std::vector<double> values(steps + 1);

    for (int i = 0; i <= steps; ++i) {
        double S = spot * std::pow(u, steps - i) * std::pow(d, i);
        values[i] = is_call ? std::max(S - strike, 0.0)
                            : std::max(strike - S, 0.0);
    }

    for (int step = steps - 1; step >= 0; --step) {
        for (int i = 0; i <= step; ++i) {
            values[i] = disc * (p * values[i] + (1.0 - p) * values[i + 1]);
            if (is_american) {
                double S = spot * std::pow(u, step - i) * std::pow(d, i);
                double intrinsic = is_call ? std::max(S - strike, 0.0)
                                           : std::max(strike - S, 0.0);
                values[i] = std::max(values[i], intrinsic);
            }
        }
    }
    return values[0];
}

double heston_price_cpp(double spot, double strike, double rate,
                         double vol, double maturity, bool is_call,
                         int num_sims, double kappa, double sigma, double rho) {
    constexpr int steps = 100;
    double dt           = maturity / steps;
    double long_run_var = vol * vol;
    double sqrt_1_rho2  = std::sqrt(1.0 - rho * rho);

    std::mt19937_64 rng(42);
    std::normal_distribution<double> norm(0.0, 1.0);

    double payoff_sum = 0.0;

    for (int sim = 0; sim < num_sims; ++sim) {
        double S = spot;
        double V = vol * vol;

        for (int t = 0; t < steps; ++t) {
            double z1 = norm(rng);
            double z2 = norm(rng);
            double w1 = z1;
            double w2 = rho * z1 + sqrt_1_rho2 * z2;

            double V_pos = std::max(V, 0.0);
            V = std::max(V + kappa * (long_run_var - V) * dt
                           + sigma * std::sqrt(V_pos * dt) * w2, 0.0);
            S *= std::exp((rate - 0.5 * V_pos) * dt
                          + std::sqrt(V_pos * dt) * w1);
        }

        payoff_sum += is_call ? std::max(S - strike, 0.0)
                              : std::max(strike - S, 0.0);
    }

    return std::exp(-rate * maturity) * payoff_sum / num_sims;
}
