#include "threebody.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

#ifdef __FAST_MATH__
#error "Native reference must be built without fast math"
#endif

namespace threebody {
static_assert(std::numeric_limits<double>::is_iec559 && std::numeric_limits<double>::digits == 53,
              "Native reference requires IEEE-754 binary64 double");
namespace {
constexpr auto infinity = std::numeric_limits<double>::infinity();
std::uint64_t choose2(std::uint64_t n) { return n * (n - 1) / 2; }
std::uint64_t choose3(std::uint64_t n) { return n * (n - 1) * (n - 2) / 6; }
void finite(const Vec6& values) {
  for (double value : values)
    if (!std::isfinite(value)) throw std::invalid_argument("State components must be finite");
}
void representable_pairs(const Vec6& p) {
  for (int i = 0; i < 3; ++i) for (int j = i + 1; j < 3; ++j) {
    const double x = p[2*j] - p[2*i], y = p[2*j+1] - p[2*i+1];
    if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(std::hypot(x,y)))
      throw std::invalid_argument("Pair separation is not representable in FP64");
  }
}
std::optional<Vec6> acc_impl(const Vec6& p) {
  Vec6 a{};
  for (int i = 0; i < 3; ++i) for (int j = i + 1; j < 3; ++j) {
    const double x = p[2*j] - p[2*i], y = p[2*j+1] - p[2*i+1];
    const double r = std::hypot(x, y);
    if (r < CLOSE) return std::nullopt;
    const double f = MU / (r * r * r);
    a[2*i] += f*x; a[2*i+1] += f*y;
    a[2*j] -= f*x; a[2*j+1] -= f*y;
  }
  return a;
}
double energy_impl(const State& state) {
  double e = 0;
  for (double x : state.v) e += x*x/2;
  for (int i = 0; i < 3; ++i) for (int j = i + 1; j < 3; ++j)
    e -= MU / std::hypot(state.p[2*i]-state.p[2*j], state.p[2*i+1]-state.p[2*j+1]);
  return e;
}
double checked_energy(const State& state) {
  // An exactly coincident pair has a natural -Inf potential diagnostic.
  // Overflow of finite kinetic/potential arithmetic is a different condition.
  double e = 0;
  for (double x : state.v) {
    const double term = x*x/2;
    e += term;
    if (!std::isfinite(term) || !std::isfinite(e))
      throw std::invalid_argument("Kinetic energy arithmetic is not representable in FP64");
  }
  bool singular = false;
  for (int i = 0; i < 3; ++i) for (int j = i + 1; j < 3; ++j) {
    const double r = std::hypot(state.p[2*i]-state.p[2*j],state.p[2*i+1]-state.p[2*j+1]);
    if (r == 0) { singular = true; continue; }
    const double term = MU/r;
    e -= term;
    if (!std::isfinite(r) || !std::isfinite(term) || !std::isfinite(e))
      throw std::invalid_argument("Potential energy arithmetic is not representable in FP64");
  }
  return singular ? -infinity : e;
}
std::array<double, 7> frame(double time, const Vec6& p) {
  return {time,p[0],p[1],p[2],p[3],p[4],p[5]};
}
bool all_finite(const State& state) {
  for (double x : state.p) if (!std::isfinite(x)) return false;
  for (double x : state.v) if (!std::isfinite(x)) return false;
  return true;
}
}

Grid grid(double radius) {
  if (!std::isfinite(radius) || radius < .1 || radius > 2)
    throw std::invalid_argument("Radius must be between 0.1 and 2 metres");
  const auto n = static_cast<std::uint64_t>(std::floor((12 - 2*radius)/radius + 1e-8)) + 1;
  const auto N = n*n;
  return {radius,n,N,choose3(N)};
}

std::array<std::uint64_t, 3> triple_at(std::uint64_t N, std::uint64_t ordinal) {
  if (N < 3 || N > 14161) throw std::invalid_argument("N must be in [3,14161]");
  if (ordinal >= choose3(N)) throw std::out_of_range("Scan ordinal out of range");
  std::uint64_t lo = 0, hi = N - 3;
  while (lo < hi) {
    const auto m = (lo + hi + 1)/2;
    if (choose3(N) - choose3(N - m) <= ordinal) lo = m; else hi = m - 1;
  }
  const auto a = lo;
  ordinal -= choose3(N) - choose3(N-a);
  lo = a + 1; hi = N - 2;
  while (lo < hi) {
    const auto m = (lo + hi + 1)/2;
    if (choose2(N-a-1) - choose2(N-m) <= ordinal) lo = m; else hi = m - 1;
  }
  const auto b = lo;
  ordinal -= choose2(N-a-1) - choose2(N-b);
  return {a,b,b+1+ordinal};
}

State initial(double radius, std::uint64_t ordinal) {
  const auto s = grid(radius);
  const auto triple = triple_at(s.N, ordinal);
  State state{};
  for (std::size_t i = 0; i < 3; ++i) {
    const auto cell = triple[i];
    state.p[2*i] = -6 + radius + static_cast<double>(cell%s.n)*radius;
    state.p[2*i+1] = 6 - radius - static_cast<double>(cell/s.n)*radius;
  }
  return state;
}

State fixture(const std::string& name) {
  if (name == "asymmetric-rest") return {{-3,-2,1,-1,2,3},{}};
  if (name == "collinear-rest") return {{-2,0,0,0,2,0},{}};
  if (name == "fast-escape") return {{-2,0,0,0,2,0},{-20,0,0,0,20,0}};
  if (name == "figure-eight") {
    const double s = 2, k = std::sqrt(MU/s);
    return {{-.97000436*s,.24308753*s,.97000436*s,-.24308753*s,0,0},
            {.466203685*k,.43236573*k,.466203685*k,.43236573*k,-.93240737*k,-.86473146*k}};
  }
  if (name == "lagrange-triangle") {
    State state{};
    const double r = 2, w = std::sqrt(MU/(std::sqrt(3.0)*r*r*r));
    const double pi = std::acos(-1.0);
    for (int i = 0; i < 3; ++i) {
      const double t = i*2*pi/3;
      state.p[2*i] = r*std::cos(t); state.p[2*i+1] = r*std::sin(t);
      state.v[2*i] = -w*r*std::sin(t); state.v[2*i+1] = w*r*std::cos(t);
    }
    return state;
  }
  throw std::invalid_argument("Unknown comparison fixture");
}

std::optional<Vec6> acceleration(const Vec6& positions) {
  finite(positions);
  // Finite coordinates can still overflow during subtraction or norm evaluation.
  // Validate the public query boundary without changing the integrator's private
  // event ordering and its Numerical error classification for transient states.
  representable_pairs(positions);
  const auto result = acc_impl(positions);
  if (result) finite(*result);
  return result;
}
double energy(const State& state) {
  finite(state.p); finite(state.v); representable_pairs(state.p);
  return checked_energy(state);
}

Result simulate(const State& input, Options options) {
  finite(input.p); finite(input.v);
  if (!std::isfinite(options.duration) || options.duration <= 0 || options.duration > 300 ||
      !std::isfinite(options.dt) || options.dt <= 0 || options.dt > .002)
    throw std::invalid_argument("Invalid duration or timestep");
  State state = input;
  Result result{};
  result.initial = input;
  representable_pairs(input.p);
  result.initial_energy = checked_energy(input);
  result.min_separation = infinity;
  result.frames.push_back(frame(0, state.p));
  result.velocity_frames.push_back(state.v);
  double sample_gap = std::min(options.duration/600, .001), next = sample_gap;
  while (result.outcome.empty()) {
    const auto a = acc_impl(state.p);
    if (!a) { result.outcome = "Close encounter"; break; }
    double distance = infinity;
    for (int i = 0; i < 3; ++i) for (int j = i + 1; j < 3; ++j)
      distance = std::min(distance, std::hypot(state.p[2*i]-state.p[2*j],state.p[2*i+1]-state.p[2*j+1]));
    result.min_separation = std::min(result.min_separation, distance);
    const double h = std::min({options.dt,.002*std::sqrt(distance*distance*distance/MU), options.duration-result.time});
    if (h < 1e-10 || result.steps > 2000000) { result.outcome = "Unresolved"; break; }
    for (std::size_t i = 0; i < 6; ++i) {
      state.v[i] += (*a)[i]*h/2;
      state.p[i] += state.v[i]*h;
    }
    if (!all_finite(state)) throw std::invalid_argument("Dynamic state arithmetic is not representable in FP64");
    representable_pairs(state.p);
    const auto b = acc_impl(state.p);
    result.time += h; ++result.steps;
    if (!b) { result.outcome = "Close encounter"; break; }
    for (std::size_t i = 0; i < 6; ++i) state.v[i] += (*b)[i]*h/2;
    if (!all_finite(state)) throw std::invalid_argument("Dynamic state arithmetic is not representable in FP64");
    const double drift = std::abs(energy_impl(state)-result.initial_energy)/std::max(std::abs(result.initial_energy), MU);
    result.energy_error = std::isnan(drift) ? drift : std::max(result.energy_error, drift);
    bool escaped = false;
    for (double x : state.p) if (std::abs(x) > LIMIT) escaped = true;
    if (escaped) { result.outcome = "Escaped"; break; }
    if (result.energy_error > .01) { result.outcome = "Numerical error"; break; }
    if (result.time >= next) {
      result.frames.push_back(frame(result.time, state.p));
      result.velocity_frames.push_back(state.v);
      next += sample_gap;
      if (result.frames.size() >= 1200) {
        std::size_t output = 0;
        for (std::size_t i = 0; i < result.frames.size(); i += 2, ++output) {
          result.frames[output] = result.frames[i];
          result.velocity_frames[output] = result.velocity_frames[i];
        }
        result.frames.resize(output); result.velocity_frames.resize(output);
        sample_gap *= 2; next = result.time + sample_gap;
      }
    }
    if (result.time >= options.duration-1e-10) result.outcome = "Bounded";
  }
  if (result.frames.back()[0] != result.time) {
    result.frames.push_back(frame(result.time, state.p));
    result.velocity_frames.push_back(state.v);
  }
  result.final = state;
  result.final_energy = checked_energy(state);
  return result;
}
}
