// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "phreak_engine.h"

// Test-only descriptor: never compiled into the package or exposed as a control.
const plaits::phreak::ToneEntry kSyntheticEntries[] = {
  { "fixture-pair", 2, { 400.0f, 450.0f }, 0.250f, 0.750f }
};
const plaits::phreak::TonePlan kSynthetic = {
  "synthetic-test-only", kSyntheticEntries, 1
};

bool RenderAudio(plaits::Engine& engine,
    plaits::EngineParameters parameters, size_t frames, FILE* output,
    size_t block_size = plaits::kBlockSize) {
  if (block_size == 0 || block_size > 24) return false;
  for (size_t position = 0; position < frames;) {
    float main[24], aux[24];
    float interleaved[48];
    const size_t remaining = frames - position;
    const size_t size = remaining < block_size ? remaining : block_size;
    bool enveloped = false;
    engine.Render(parameters, main, aux, size, &enveloped);
    if (!enveloped) return false;
    parameters.trigger &= ~plaits::TRIGGER_RISING_EDGE;
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
  if (argc == 6 && (std::strcmp(argv[1], "bursts") == 0
      || std::strcmp(argv[1], "lpg-reference") == 0)) {
    const int index = std::atoi(argv[2]);
    const int seconds = std::atoi(argv[3]);
    const size_t block = static_cast<size_t>(std::atoi(argv[5]));
    if ((index != 5 && index != 13 && index != 14)
        || seconds < 1 || seconds > 3 || block == 0 || block > 24) return 1;
    FILE* output = std::fopen(argv[4], "wb");
    if (!output) return 1;
    if (std::strcmp(argv[1], "bursts") == 0) {
      plaits::PhreakEngine engine;
      engine.Init(NULL);
      plaits::EngineParameters p = plaits::EngineParameters();
      p.note = 60.0f;
      p.harmonics = (index + 0.5f) / 21.0f;
      p.morph = p.macro = 0.5f;
      for (int edge = 0; edge < seconds * 2; ++edge) {
        // Like the SDK's 2 Hz trigger, high for 1/4 of each period.
        p.trigger = plaits::TRIGGER_RISING_EDGE | plaits::TRIGGER_HIGH;
        if (!RenderAudio(engine, p, 6000, output, block)) return 1;
        p.trigger = plaits::TRIGGER_LOW;
        if (!RenderAudio(engine, p, 18000, output, block)) return 1;
      }
    } else {
      // Independent test oracle: no package voice, cadence or contour helpers.
      // Use the repository's oscillator primitive to preserve float phase
      // arithmetic, and literal normative Hz and sample times at 48 kHz.
      const float hz0 = index == 5 ? 770.0f : index == 13 ? 480.0f : 440.0f;
      const float hz1 = index == 5 ? 1336.0f : index == 13 ? 620.0f : 480.0f;
      float phase0 = 0.0f, phase1 = 0.0f;
      plaits::LowPassGate lpg;
      lpg.Init();
      for (int n = 0; n < seconds * 48000; ++n) {
        phase0 += hz0 / 48000.0f;
        phase1 += hz1 / 48000.0f;
        phase0 -= static_cast<int>(phase0);
        phase1 -= static_cast<int>(phase1);
        const int age = n % 24000;
        float samples[2] = { 0.0f, 0.0f };
        if (age < 4800) {
          const float e = age < 48 ? age / 48.0f
              : age < 4608 ? 1.0f : (4800 - age) / 192.0f;
          const float taper = age < 4608 ? 1.0f : (4800 - age) / 192.0f;
          samples[0] = 0.25f * (plaits::Sine(phase0) + plaits::Sine(phase1));
          samples[1] = samples[0] * e * taper;  // Amplitude-only negative oracle.
          lpg.Process(e, 0.003f + 0.3f * (e * e) * (e * e), 0.0f, samples, 1);
          samples[0] *= taper;
        } else {
          lpg.Init();
        }
        if (std::fwrite(samples, sizeof(float), 2, output) != 2) return 1;
      }
    }
    return std::fclose(output) == 0 ? 0 : 1;
  }
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
  if (argc == 5 && std::strcmp(argv[1], "helper") == 0) {
    const bool synthetic = std::strcmp(argv[2], "synthetic") == 0;
    const int index = std::atoi(argv[2]);
    const double seconds = std::atof(argv[3]);
    if ((!synthetic && (index < 0 || index >= static_cast<int>(plan.count)))
        || !(seconds > 0.0 && seconds <= 12.0)) return 1;
    const plaits::phreak::TonePlan& fixture = synthetic ? kSynthetic : plan;
    plaits::phreak::ToneEntry entry = fixture.entries[synthetic ? 0 : index];
    plaits::phreak::ToneVoice cadenced, continuous;
    cadenced.SetTone(entry);
    entry.on_seconds = entry.off_seconds = 0.0f;
    continuous.SetTone(entry);
    FILE* output = std::fopen(argv[4], "wb");
    if (!output) return 1;
    const size_t frames = static_cast<size_t>(seconds * plaits::kSampleRate);
    for (size_t i = 0; i < frames; ++i) {
      // Helper/reference pair, not the engine's MAIN/AUX channels.
      const float samples[] = { cadenced.Next(), continuous.Next() };
      if (std::fwrite(samples, sizeof(float), 2, output) != 2) {
        std::fclose(output);
        return 1;
      }
    }
    return std::fclose(output) == 0 ? 0 : 1;
  }
  const bool steps = argc >= 5 && std::strcmp(argv[1], "steps") == 0;
  const bool timeline = argc >= 6 && std::strcmp(argv[1], "timeline") == 0;
  if (!steps && !timeline && argc != 4) {
    std::fprintf(stderr,
        "usage: %s table | index HARMONICS | HARMONICS SECONDS OUTPUT\n"
        "       %s steps SECONDS_PER_STEP OUTPUT HARMONICS [HARMONICS | reset ...]\n"
        "       %s timeline BLOCK_SIZE OUTPUT [note=MIDI] HARMONICS FRAMES [HARMONICS FRAMES | reset ...]\n"
        "       %s helper INDEX_OR_synthetic SECONDS OUTPUT\n"
        "       %s bursts|lpg-reference INDEX SECONDS OUTPUT BLOCK_SIZE\n",
        argv[0], argv[0], argv[0], argv[0], argv[0]);
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
    if ((steps || timeline) && std::strncmp(argv[step], "note=", 5) == 0) {
      parameters.note = static_cast<float>(std::atof(argv[step] + 5));
      continue;
    }
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
