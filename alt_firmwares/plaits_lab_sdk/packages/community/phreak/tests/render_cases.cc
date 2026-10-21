// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "phreak_engine.h"

// Host-only driver. Audio is interleaved native float MAIN/AUX at 48 kHz.
int main(int argc, char** argv) {
  const plaits::phreak::TonePlan& plan = plaits::phreak::kNorthAmerica;
  if (argc == 2 && std::strcmp(argv[1], "table") == 0) {
    std::printf("%s %lu\n", plan.locale,
        static_cast<unsigned long>(plan.count));
    for (size_t i = 0; i < plan.count; ++i) {
      const plaits::phreak::ToneEntry& entry = plan.entries[i];
      std::printf("%s %lu %g %g %g %g\n", entry.label,
          static_cast<unsigned long>(entry.oscillator_count),
          entry.frequency_hz[0], entry.frequency_hz[1],
          entry.on_seconds, entry.off_seconds);
    }
    return 0;
  }
  if (argc != 4) {
    std::fprintf(stderr, "usage: %s table | HARMONICS SECONDS OUTPUT\n", argv[0]);
    return 1;
  }
  const double seconds = std::atof(argv[2]);
  if (!(seconds > 0.0 && seconds <= 12.0)) return 1;
  const size_t frames = static_cast<size_t>(seconds * plaits::kSampleRate);
  FILE* output = std::fopen(argv[3], "wb");
  if (!output) return 1;
  plaits::EngineParameters parameters = plaits::EngineParameters();
  parameters.note = 60.0f;
  parameters.harmonics = static_cast<float>(std::atof(argv[1]));
  parameters.timbre = 0.0f;
  parameters.morph = parameters.macro = 0.5f;
  parameters.trigger = plaits::TRIGGER_UNPATCHED;
  plaits::PhreakEngine engine;
  engine.Init(NULL);  // The package needs no allocator storage.
  for (size_t position = 0; position < frames;) {
    float main[plaits::kBlockSize], aux[plaits::kBlockSize];
    float interleaved[2 * plaits::kBlockSize];
    const size_t remaining = frames - position;
    const size_t size = remaining < plaits::kBlockSize
        ? remaining : plaits::kBlockSize;
    bool enveloped = false;
    engine.Render(parameters, main, aux, size, &enveloped);
    for (size_t i = 0; i < size; ++i) {
      interleaved[2 * i] = main[i];
      interleaved[2 * i + 1] = aux[i];
    }
    if (std::fwrite(interleaved, sizeof(float), 2 * size, output) != 2 * size) {
      std::fclose(output);
      return 1;
    }
    position += size;
  }
  return std::fclose(output) == 0 ? 0 : 1;
}
