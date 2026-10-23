#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace threebody {
inline constexpr double MU = 9.80665, LIMIT = 6.0, CLOSE = 0.015;
using Vec6 = std::array<double, 6>;
struct State { Vec6 p{}, v{}; };
struct Options { double duration = 30.0, dt = 0.002; };
struct Grid { double radius; std::uint64_t n, N, total; };
struct Result {
  State initial, final;
  std::string outcome;
  double time = 0, energy_error = 0, min_separation = 0;
  double initial_energy = 0, final_energy = 0;
  std::uint64_t steps = 0;
  std::vector<std::array<double, 7>> frames;
  std::vector<Vec6> velocity_frames;
};
Grid grid(double radius);
std::array<std::uint64_t, 3> triple_at(std::uint64_t N, std::uint64_t ordinal);
State initial(double radius, std::uint64_t ordinal);
State fixture(const std::string& name);
std::optional<Vec6> acceleration(const Vec6& positions);
double energy(const State& state);
Result simulate(const State& state, Options options = {});
}
