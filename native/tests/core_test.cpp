#include "threebody.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace threebody;
namespace {
bool near(double a, double b, double tolerance = 1e-12) { return std::abs(a-b) <= tolerance; }
template<class Function> void rejects(Function f) {
  bool rejected = false;
  try { f(); } catch (const std::invalid_argument&) { rejected = true; }
  catch (const std::out_of_range&) { rejected = true; }
  assert(rejected);
}
}
int main() {
  // Exhaustive enumeration is independent of the unranking implementation.
  for (std::uint64_t n = 3; n < 35; ++n) {
    std::uint64_t rank = 0;
    for (std::uint64_t a = 0; a < n-2; ++a)
      for (std::uint64_t b = a+1; b < n-1; ++b)
        for (std::uint64_t c = b+1; c < n; ++c)
          assert((triple_at(n,rank++) == std::array<std::uint64_t,3>{a,b,c}));
    assert(rank == n*(n-1)*(n-2)/6);
    rejects([&]{triple_at(n,rank);});
  }
  assert(grid(.25).total == 1794096784);
  assert(grid(.1).N == 14161);
  assert((initial(.25,0).p == Vec6{-5.75,5.75,-5.5,5.75,-5.25,5.75}));
  assert((triple_at(14161,grid(.1).total-1) == std::array<std::uint64_t,3>{14158,14159,14160}));
  rejects([]{grid(std::numeric_limits<double>::quiet_NaN());});
  rejects([]{grid(.099);}); rejects([]{grid(2.01);});
  rejects([]{triple_at(2,0);}); rejects([]{triple_at(14162,0);});
  rejects([]{triple_at(std::numeric_limits<std::uint64_t>::max(),0);});
  rejects([]{fixture("not-a-fixture");});
  const auto symmetric = acceleration(fixture("collinear-rest").p).value();
  assert(symmetric[2] == 0 && symmetric[3] == 0);
  assert(near(symmetric[0],MU/4+MU/16));
  assert(near(symmetric[4],-symmetric[0]));
  // Linear superposition isolates the contribution at one and two metres.
  const auto unit = acceleration({0,0,1,0,0,10}).value();
  const auto doubled = acceleration({0,0,2,0,0,10}).value();
  assert(near(unit[0],MU)); assert(near(doubled[0],MU/4));
  assert(near(unit[1],MU/100));
  const State rest = fixture("asymmetric-rest");
  const auto a = acceleration(rest.p).value();
  assert(near(a[0]+a[2]+a[4],0)); assert(near(a[1]+a[3]+a[5],0));
  const auto short_run = simulate(rest,{.1,.002});
  assert(short_run.outcome == "Bounded" && near(short_run.time,.1));
  for (int i = 0; i < 3; ++i)
    assert(std::hypot(short_run.final.p[2*i]-rest.p[2*i],short_run.final.p[2*i+1]-rest.p[2*i+1]) > 0);
  assert((rest.p == fixture("asymmetric-rest").p));
  const auto repeated = simulate(rest,{.1,.002});
  assert(short_run.final.p == repeated.final.p && short_run.final.v == repeated.final.v);
  assert(short_run.frames.size() == short_run.velocity_frames.size());
  assert(short_run.frames.front()[0] == 0 && short_run.frames.back()[0] == short_run.time);
  assert(short_run.energy_error < 1e-5);
  const auto collapse = simulate(initial(.25,0),{6,.002});
  assert(collapse.outcome == "Close encounter");
  const auto escaped = simulate(initial(2,57),{6,.002});
  assert(escaped.outcome == "Escaped" && escaped.time < 5);
  const auto launched = simulate(fixture("fast-escape"),{1,.002});
  assert(launched.outcome == "Escaped");
  const auto eight = simulate(fixture("figure-eight"),{30,.002});
  assert(eight.outcome == "Bounded" && eight.frames.size() <= 1201);
  assert(eight.frames.size() == eight.velocity_frames.size());
  const auto triangle = simulate(fixture("lagrange-triangle"),{1,.002});
  assert(triangle.outcome == "Bounded");
  // Singular states stop as close encounters; no softening or merger occurs.
  State singular{{0,0,0,0,1,1},{}};
  assert(!acceleration(singular.p));
  const auto contact = simulate(singular);
  assert(contact.outcome == "Close encounter" && contact.time == 0 && contact.steps == 0);
  assert(std::isinf(contact.initial_energy));
  assert(contact.frames.size() == 1 && std::isinf(contact.min_separation));
  rejects([&]{simulate(rest,{0,.002});}); rejects([&]{simulate(rest,{1,0});});
  rejects([&]{simulate(rest,{301,.002});}); rejects([&]{simulate(rest,{1,.003});});
  State invalid = rest; invalid.p[0] = std::numeric_limits<double>::infinity();
  rejects([&]{simulate(invalid);}); rejects([&]{energy(invalid);});
  rejects([&]{acceleration(invalid.p);});
  // Finite inputs must never leak nonfinite components through the public API.
  rejects([]{acceleration({1e308,0,-1e308,0,0,1e308});});
  rejects([]{acceleration({1.3e308,1.3e308,0,0,-1,0});});
  const State overflowing{{std::numeric_limits<double>::max(),0,0,1,0,-1},{1e308,0,0,0,0,0}};
  rejects([&]{simulate(overflowing,{.01,.002});});
  rejects([&]{energy(overflowing);});
  assert(overflowing.p[0] == std::numeric_limits<double>::max() && overflowing.v[0] == 1e308);
  const auto unresolved = simulate(rest,{1,1e-12});
  assert(unresolved.outcome == "Unresolved" && unresolved.steps == 0);
  std::cout << "PASS: native analytic forces, conservation, all-rest motion, exhaustive unranking, replay endpoints, reference fixtures, singular stops and input bounds\n";
}
