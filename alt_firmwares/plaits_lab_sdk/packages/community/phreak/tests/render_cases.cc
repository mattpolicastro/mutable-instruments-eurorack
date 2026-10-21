// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "phreak_engine.h"

bool RenderAudio(plaits::Engine& engine,
    const plaits::EngineParameters& parameters, size_t frames, FILE* output,
    size_t block_size = plaits::kBlockSize) {
  if (block_size == 0 || block_size > 24) return false;
  for (size_t position = 0; position < frames;) {
    float main[24], aux[24];
    float interleaved[48];
    const size_t remaining = frames - position;
    const size_t size = remaining < block_size ? remaining : block_size;
    bool enveloped = false;
    engine.Render(parameters, main, aux, size, &enveloped);
    for (size_t i = 0; i < size; ++i) {
      interleaved[2 * i] = main[i];
      interleaved[2 * i + 1] = aux[i];
    }
    if (std::fwrite(interleaved, sizeof(float), 2 * size, output) != 2 * size) {
      return false;
    }
    position += size;
  }
  return true;
}

// Host-only driver. Audio is interleaved native float MAIN/AUX at 48 kHz.
int main(int argc, char** argv) {
  const plaits::phreak::TonePlan& plan = plaits::phreak::kNorthAmerica;
  if (argc == 3 && std::strcmp(argv[1], "index") == 0) {
    // Observe the selector without dereferencing a potentially invalid index.
    const float harmonics = static_cast<float>(std::atof(argv[2]));
    std::printf("%lu\n", static_cast<unsigned long>(
        plaits::phreak::NominalToneIndex(plan, harmonics)));
    return 0;
  }
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
  const bool steps = argc >= 5 && std::strcmp(argv[1], "steps") == 0;
  const bool timeline = argc >= 6 && std::strcmp(argv[1], "timeline") == 0;
  if (!steps && !timeline && argc != 4) {
    std::fprintf(stderr,
        "usage: %s table | index HARMONICS | HARMONICS SECONDS OUTPUT\n"
        "       %s steps SECONDS_PER_STEP OUTPUT HARMONICS [HARMONICS | reset ...]\n"
        "       %s timeline BLOCK_SIZE OUTPUT HARMONICS FRAMES [HARMONICS FRAMES | reset ...]\n",
        argv[0], argv[0], argv[0]);
    return 1;
  }
  const double seconds = std::atof(argv[2]);
  if (!timeline && !(seconds > 0.0 && seconds <= 12.0)) return 1;
  const size_t block_size = timeline
      ? static_cast<size_t>(std::atoi(argv[2])) : plaits::kBlockSize;
  if (block_size == 0 || block_size > 24) return 1;
  const size_t frames = static_cast<size_t>(seconds * plaits::kSampleRate);
  FILE* output = std::fopen(argv[3], "wb");
  if (!output) return 1;
  plaits::EngineParameters parameters = plaits::EngineParameters();
  parameters.note = 60.0f;
  parameters.timbre = 0.0f;
  parameters.morph = parameters.macro = 0.5f;
  parameters.trigger = plaits::TRIGGER_UNPATCHED;
  plaits::PhreakEngine engine;
  engine.Init(NULL);  // The package needs no allocator storage.
  const int first = steps || timeline ? 4 : 1;
  const int last = steps || timeline ? argc : 2;
  for (int step = first; step < last; ++step) {
    if ((steps || timeline) && std::strcmp(argv[step], "reset") == 0) {
      engine.Reset();
      continue;
    }
    parameters.harmonics = static_cast<float>(std::atof(argv[step]));
    size_t step_frames = frames;
    if (timeline) {
      if (++step == last) {
        std::fclose(output);
        return 1;
      }
      const int count = std::atoi(argv[step]);
      if (count <= 0 || count > 12 * 48000) {
        std::fclose(output);
        return 1;
      }
      step_frames = static_cast<size_t>(count);
    }
    if (!RenderAudio(engine, parameters, step_frames, output, block_size)) {
      std::fclose(output);
      return 1;
    }
  }
  return std::fclose(output) == 0 ? 0 : 1;
}
