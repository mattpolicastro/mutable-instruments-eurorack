// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "stmlib/utils/buffer_allocator.h"

#include "phreak_engine.h"

// Host-only test driver; it is not linked into the engine.
//
//   render_cases table
//     Every system, entry and step, one per line.
//   render_cases timeline BLOCK OUTPUT TOKEN...
//     Renders interleaved native float MAIN/AUX at 48 kHz, BLOCK samples per
//     Render call. Tokens set controls (h=, t=, m=, x= for HARMONICS, TIMBRE,
//     MORPH, macro; n= for the MIDI note), set TRIG (trig=unpatched, trig=low,
//     trig=high; low to high is a rising edge on the next block), reset the
//     engine (reset), or render a number of frames.

namespace {

int Table() {
  for (size_t s = 0; s < plaits::phreak::kNumPlans; ++s) {
    const plaits::phreak::TonePlan& plan = *plaits::phreak::kPlans[s];
    std::printf("system %s %lu\n", plan.locale, static_cast<unsigned long>(plan.count));
    for (size_t e = 0; e < plan.count; ++e) {
      const plaits::phreak::ToneEntry& entry = plan.entries[e];
      std::printf("entry %s %lu\n", entry.label,
          static_cast<unsigned long>(entry.num_steps));
      for (size_t i = 0; i < entry.num_steps; ++i) {
        const plaits::phreak::Step& step = entry.steps[i];
        std::printf("step %g %d %g %g %g %g %g\n", step.seconds, step.signal,
            step.hz[0], step.hz[1], step.hz[2], step.hz[3], step.rate);
      }
    }
  }
  return 0;
}

int Timeline(int argc, char** argv) {
  const size_t block = static_cast<size_t>(std::atoi(argv[2]));
  const size_t kMaxBlock = 64;
  if (block == 0 || block > kMaxBlock) return 1;
  FILE* output = std::fopen(argv[3], "wb");
  if (!output) return 1;

  static char memory[16384];
  stmlib::BufferAllocator allocator(memory, sizeof(memory));
  plaits::PhreakEngine engine;
  engine.Init(&allocator);
  plaits::EngineParameters parameters = plaits::EngineParameters();
  parameters.note = 60.0f;
  parameters.harmonics = 0.0f;
  parameters.timbre = 0.5f;
  parameters.morph = 0.0f;
  parameters.macro = 0.5f;
  parameters.accent = 0.8f;

  bool patched = false;
  bool high = false;
  bool edge = false;
  float main[kMaxBlock];
  float aux[kMaxBlock];
  for (int i = 4; i < argc; ++i) {
    const char* token = argv[i];
    const float value = static_cast<float>(std::atof(token + 2));
    if (std::strcmp(token, "reset") == 0) {
      engine.Reset();
    } else if (std::strcmp(token, "trig=unpatched") == 0) {
      patched = high = false;
    } else if (std::strcmp(token, "trig=low") == 0) {
      patched = true;
      high = false;
    } else if (std::strcmp(token, "trig=high") == 0) {
      edge = edge || !high;
      patched = high = true;
    } else if (std::strncmp(token, "h=", 2) == 0) {
      parameters.harmonics = value;
    } else if (std::strncmp(token, "t=", 2) == 0) {
      parameters.timbre = value;
    } else if (std::strncmp(token, "m=", 2) == 0) {
      parameters.morph = value;
    } else if (std::strncmp(token, "x=", 2) == 0) {
      parameters.macro = value;
    } else if (std::strncmp(token, "n=", 2) == 0) {
      parameters.note = value;
    } else {
      size_t frames = static_cast<size_t>(std::atol(token));
      while (frames) {
        const size_t size = frames < block ? frames : block;
        if (!patched) {
          parameters.trigger = plaits::TRIGGER_UNPATCHED;
        } else {
          parameters.trigger = (high ? plaits::TRIGGER_HIGH : plaits::TRIGGER_LOW)
              | (edge ? plaits::TRIGGER_RISING_EDGE : 0);
          edge = false;
        }
        bool enveloped = false;
        engine.Render(parameters, main, aux, size, &enveloped);
        for (size_t n = 0; n < size; ++n) {
          std::fwrite(&main[n], sizeof(float), 1, output);
          std::fwrite(&aux[n], sizeof(float), 1, output);
        }
        frames -= size;
      }
    }
  }
  std::fclose(output);
  return 0;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc == 2 && std::strcmp(argv[1], "table") == 0) return Table();
  if (argc >= 4 && std::strcmp(argv[1], "timeline") == 0) return Timeline(argc, argv);
  std::fprintf(stderr, "usage: %s table | timeline BLOCK OUTPUT TOKEN...\n", argv[0]);
  return 1;
}
