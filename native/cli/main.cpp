#include "threebody.hpp"

#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <locale>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>

#if defined(__FAST_MATH__) || defined(_M_FP_FAST)
#error "The native reference must be compiled without fast math"
#endif
#if defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__ != 0
#error "The native reference requires nonfinite-value checks"
#endif
static_assert(std::numeric_limits<double>::is_iec559 &&
              std::numeric_limits<double>::digits == 53,
              "The native reference requires IEEE-754 binary64 doubles");

namespace {
using threebody::State;

std::string quoted(const std::string& value) {
  std::ostringstream out;
  out << '"';
  for (unsigned char ch : value) {
    switch (ch) {
      case '"': out << "\\\""; break;
      case '\\': out << "\\\\"; break;
      case '\b': out << "\\b"; break;
      case '\f': out << "\\f"; break;
      case '\n': out << "\\n"; break;
      case '\r': out << "\\r"; break;
      case '\t': out << "\\t"; break;
      default:
        if (ch < 0x20) {
          const char* hex = "0123456789abcdef";
          out << "\\u00" << hex[ch >> 4] << hex[ch & 15];
        } else {
          out << static_cast<char>(ch);
        }
    }
  }
  out << '"';
  return out.str();
}

double numeric(const std::string& token) {
  static const std::regex syntax(R"([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)");
  if (token.size() > 128 || !std::regex_match(token, syntax)) {
    throw std::invalid_argument("Expected a finite decimal or scientific number");
  }
  std::istringstream input(token);
  input.imbue(std::locale::classic());
  double result = 0;
  input >> std::noskipws >> result;
  if (input.fail() || !input.eof() || !std::isfinite(result)) {
    throw std::invalid_argument("Number is outside the finite double range");
  }
  return result;
}

std::uint64_t ordinal(const std::string& token) {
  if (token.empty() || token.size() > 20 || (token.size() > 1 && token.front() == '0')) {
    throw std::invalid_argument("Ordinal must be a canonical unsigned decimal integer");
  }
  std::uint64_t result = 0;
  for (char ch : token) {
    if (ch < '0' || ch > '9') {
      throw std::invalid_argument("Ordinal must be a canonical unsigned decimal integer");
    }
    const auto digit = static_cast<unsigned>(ch - '0');
    if (result > (std::numeric_limits<std::uint64_t>::max() - digit) / 10) {
      throw std::invalid_argument("Ordinal exceeds uint64 range");
    }
    result = result * 10 + digit;
  }
  return result;
}

void number(std::ostream& out, double value) {
  if (std::isfinite(value)) out << value;
  else out << "null";
}

template<class Sequence>
void vector(std::ostream& out, const Sequence& values) {
  out << '[';
  bool first = true;
  for (const auto value : values) {
    if (!first) out << ',';
    first = false;
    number(out, value);
  }
  out << ']';
}

template<class Frames>
void matrix(std::ostream& out, const Frames& frames) {
  out << '[';
  bool first = true;
  for (const auto& frame : frames) {
    if (!first) out << ',';
    first = false;
    vector(out, frame);
  }
  out << ']';
}

void state(std::ostream& out, const State& value) {
  out << "{\"p\":";
  vector(out, value.p);
  out << ",\"v\":";
  vector(out, value.v);
  out << '}';
}

std::string compiler() {
#if defined(__clang__)
  return std::string("Clang ") + __clang_version__;
#elif defined(__GNUC__)
  return std::string("GCC ") + __VERSION__;
#elif defined(_MSC_VER)
  return std::string("MSVC ") + std::to_string(_MSC_VER);
#else
  return "unknown C++17 compiler";
#endif
}

void envelope(std::ostream& out) {
  out << "{\"protocol\":\"threebody.native-reference.v1\","
         "\"engine\":\"native-fp64-v1\",\"build\":{\"compiler\":"
      << quoted(compiler()) << ",\"precision\":\"fp64\",\"fast_math\":false}";
}

struct Arguments {
  std::string operation = "simulate", fixture;
  double radius = .25;
  std::uint64_t index = 0;
  threebody::Options options;
  threebody::Vec6 positions{};
  std::set<std::string> seen;
};

Arguments parse(int argc, char** argv) {
  Arguments result;
  for (int i = 1; i < argc; ++i) {
    const std::string flag(argv[i]);
    if (!result.seen.insert(flag).second) throw std::invalid_argument("Duplicate flag: " + flag);
    auto value = [&]() -> std::string {
      if (i + 1 >= argc) throw std::invalid_argument("Missing value for " + flag);
      return argv[++i];
    };
    if (flag == "--radius") result.radius = numeric(value());
    else if (flag == "--ordinal") result.index = ordinal(value());
    else if (flag == "--duration") result.options.duration = numeric(value());
    else if (flag == "--dt") result.options.dt = numeric(value());
    else if (flag == "--fixture") result.fixture = value();
    else if (flag == "--describe" || flag == "--initial" || flag == "--acceleration") {
      if (result.operation != "simulate") throw std::invalid_argument("Choose exactly one operation");
      result.operation = flag.substr(2);
      if (flag == "--acceleration") {
        for (auto& component : result.positions) component = numeric(value());
      }
    // POSIX argv may contain non-UTF-8 bytes. Never reflect an unrecognized
    // token into the JSON diagnostic; all other reflected flags are known ASCII.
    } else throw std::invalid_argument("Unknown flag");
  }
  std::set<std::string> allowed;
  if (result.operation == "describe") allowed = {"--describe", "--radius"};
  else if (result.operation == "initial") allowed = {"--initial", "--radius", "--ordinal"};
  else if (result.operation == "acceleration") allowed = {"--acceleration"};
  else if (result.seen.count("--fixture")) {
    allowed = {"--fixture", "--duration", "--dt"};
    if (result.fixture.empty()) throw std::invalid_argument("Fixture name must be nonempty");
  } else allowed = {"--radius", "--ordinal", "--duration", "--dt"};
  for (const auto& flag : result.seen) {
    if (!allowed.count(flag)) throw std::invalid_argument("Flag is incompatible with selected operation: " + flag);
  }
  if (!(result.options.duration > 0 && result.options.duration <= 300) ||
      !(result.options.dt > 0 && result.options.dt <= .002)) {
    throw std::invalid_argument("Duration must be in (0,300] and timestep in (0,0.002]");
  }
  return result;
}

std::string run(const Arguments& args) {
  std::ostringstream out;
  out.imbue(std::locale::classic());
  out << std::setprecision(std::numeric_limits<double>::max_digits10);
  if (args.operation == "acceleration") {
    const auto acceleration = threebody::acceleration(args.positions);
    envelope(out);
    out << ",\"acceleration\":";
    if (acceleration) vector(out, *acceleration);
    else out << "null";
  } else if (args.operation == "describe") {
    const auto grid = threebody::grid(args.radius);
    envelope(out);
    out << ",\"grid\":{\"radius\":";
    number(out, grid.radius);
    out << ",\"n\":" << grid.n << ",\"N\":" << grid.N
        << ",\"total\":" << quoted(std::to_string(grid.total)) << '}';
  } else if (args.operation == "initial") {
    const auto grid = threebody::grid(args.radius);
    const auto initial = threebody::initial(args.radius, args.index);
    const auto triple = threebody::triple_at(grid.N, args.index);
    envelope(out);
    out << ",\"initial\":";
    state(out, initial);
    out << ",\"triple\":[" << triple[0] << ',' << triple[1] << ',' << triple[2] << ']';
  } else {
    const State initial = args.fixture.empty() ? threebody::initial(args.radius, args.index) : threebody::fixture(args.fixture);
    const auto result = threebody::simulate(initial, args.options);
    envelope(out);
    out << ",\"input\":{";
    if (args.fixture.empty()) {
      out << "\"radius\":";
      number(out, args.radius);
      out << ",\"ordinal\":" << quoted(std::to_string(args.index));
    } else out << "\"fixture\":" << quoted(args.fixture);
    out << "},\"result\":{\"engineVersion\":2,\"initial\":";
    state(out, result.initial);
    out << ",\"frames\":"; matrix(out, result.frames);
    out << ",\"velocityFrames\":"; matrix(out, result.velocity_frames);
    out << ",\"outcome\":" << quoted(result.outcome) << ",\"time\":"; number(out, result.time);
    out << ",\"energyError\":"; number(out, result.energy_error);
    out << ",\"minSeparation\":"; number(out, result.min_separation);
    out << ",\"steps\":" << result.steps << ",\"initialEnergy\":"; number(out, result.initial_energy);
    out << ",\"finalEnergy\":"; number(out, result.final_energy);
    out << ",\"finalVelocity\":"; vector(out, result.final.v);
    out << ",\"options\":{\"duration\":"; number(out, args.options.duration);
    out << ",\"dt\":"; number(out, args.options.dt);
    out << ",\"mu\":"; number(out, threebody::MU);
    out << ",\"boundary\":"; number(out, threebody::LIMIT);
    out << ",\"close\":"; number(out, threebody::CLOSE);
    out << "}}";
  }
  out << '}';
  return out.str();
}
} // namespace

int main(int argc, char** argv) {
  try {
    const auto output = run(parse(argc, argv));
    std::cout << output << '\n';
    return 0;
  } catch (const std::invalid_argument& error) {
    std::cerr << "{\"error\":{\"code\":\"invalid_input\",\"message\":" << quoted(error.what()) << "}}\n";
    return 2;
  } catch (const std::out_of_range& error) {
    std::cerr << "{\"error\":{\"code\":\"invalid_input\",\"message\":" << quoted(error.what()) << "}}\n";
    return 2;
  } catch (const std::exception&) {
    std::cerr << "{\"error\":{\"code\":\"execution_error\",\"message\":\"Native reference execution failed\"}}\n";
    return 1;
  }
}
