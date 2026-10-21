// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_TONES_H_
#define PLAITS_LAB_PHREAK_TONES_H_

#include "plaits/dsp/dsp.h"
#include "plaits/dsp/oscillator/sine_oscillator.h"
#include "phreak_articulation.h"

namespace plaits {
namespace phreak {

struct ToneEntry {
  const char* label;
  size_t oscillator_count;
  // All valid entries have at most two components; consumers use that count.
  // mutation-equivalent: [3] adds an unused zero-initialized slot, only changing storage layout.
  float frequency_hz[2];
  // Both zero means continuous; otherwise durations include the edge ramps.
  float on_seconds;
  float off_seconds;
};

struct TonePlan {
  const char* locale;
  const ToneEntry* entries;
  size_t count;
};

const ToneEntry kNorthAmericanEntries[] = {
  { "dial",      2, { 350.0f,  440.0f }, 0.0f, 0.0f },
  { "key-1",     2, { 697.0f, 1209.0f }, 0.0f, 0.0f },
  { "key-2",     2, { 697.0f, 1336.0f }, 0.0f, 0.0f },
  { "key-3",     2, { 697.0f, 1477.0f }, 0.0f, 0.0f },
  { "key-4",     2, { 770.0f, 1209.0f }, 0.0f, 0.0f },
  { "key-5",     2, { 770.0f, 1336.0f }, 0.0f, 0.0f },
  { "key-6",     2, { 770.0f, 1477.0f }, 0.0f, 0.0f },
  { "key-7",     2, { 852.0f, 1209.0f }, 0.0f, 0.0f },
  { "key-8",     2, { 852.0f, 1336.0f }, 0.0f, 0.0f },
  { "key-9",     2, { 852.0f, 1477.0f }, 0.0f, 0.0f },
  { "key-0",     2, { 941.0f, 1336.0f }, 0.0f, 0.0f },
  { "hash",      2, { 941.0f, 1477.0f }, 0.0f, 0.0f },
  { "star",      2, { 941.0f, 1209.0f }, 0.0f, 0.0f },
  { "busy",      2, { 480.0f,  620.0f }, 0.5f, 0.5f },
  { "ring",      2, { 440.0f,  480.0f }, 2.0f, 4.0f },
  { "key-a",     2, { 697.0f, 1633.0f }, 0.0f, 0.0f },
  { "key-b",     2, { 770.0f, 1633.0f }, 0.0f, 0.0f },
  { "key-c",     2, { 852.0f, 1633.0f }, 0.0f, 0.0f },
  { "key-d",     2, { 941.0f, 1633.0f }, 0.0f, 0.0f },
  { "fsk-space", 1, { 2200.0f,   0.0f }, 0.0f, 0.0f },
  { "fsk-mark",  1, { 1200.0f,   0.0f }, 0.0f, 0.0f }
};

const TonePlan kNorthAmerica = {
  "north-america", kNorthAmericanEntries,
  sizeof(kNorthAmericanEntries) / sizeof(kNorthAmericanEntries[0])
};

// Plans must be nonempty. Positive integer conversion implements floor.
inline size_t NominalToneIndex(const TonePlan& plan, float harmonics) {
  if (!(harmonics > 0.0f)) return 0;
  if (harmonics >= 1.0f) return plan.count - 1;
  const size_t index = static_cast<size_t>(harmonics * plan.count);
  return index < plan.count ? index : plan.count - 1;
}

// Retain the latest accepted request independently of oscillator state.
// A selector consumes one nonempty plan until Reset.
class ToneSelector {
 public:
  ToneSelector() { Reset(); }
  void Reset() {
    initialized_ = false;
    index_ = 0;
  }
  size_t Process(const TonePlan& plan, float harmonics) {
    if (!(harmonics > 0.0f)) harmonics = 0.0f;
    if (harmonics > 1.0f) harmonics = 1.0f;
    const float margin = 0.002f;
    if (!initialized_
        || (index_ + 1 < plan.count
            && harmonics >= static_cast<float>(index_ + 1) / plan.count + margin)
        || (index_ > 0
            && harmonics < static_cast<float>(index_) / plan.count - margin)) {
      // Jump directly to the nominal zone, even across multiple entries.
      index_ = NominalToneIndex(plan, harmonics);
      initialized_ = true;
    }
    return index_;
  }

 private:
  bool initialized_;
  size_t index_;
};

// Fixed storage for at most two sines and an independent cadence clock.
// SetTone preserves oscillator phases and restarts cadence at its on phase.
class ToneVoice {
 public:
  ToneVoice() { Reset(); }
  void Reset() {
    phase_[0] = phase_[1] = 0.0f;
    // Reset disables Next's loop; SetTone writes every active increment before use.
    // mutation-equivalent: assigning only increment_[1] leaves an unread slot until SetTone overwrites it.
    increment_[0] = increment_[1] = 0.0f;
    oscillator_count_ = 0;
    gain_ = 0.0f;
    cadence_.Reset();
  }
  void SetTone(const ToneEntry& entry) {
    cadence_.Reset(entry.on_seconds, entry.off_seconds);
    oscillator_count_ = entry.oscillator_count;
    gain_ = oscillator_count_ == 1 ? 0.5f : 0.25f;
    for (size_t i = 0; i < oscillator_count_; ++i) {
      increment_[i] = entry.frequency_hz[i] / kSampleRate;
    }
  }
  // Largest reference increment, before transposition (cycles per sample).
  float max_increment() const {
    float maximum = 0.0f;
    for (size_t i = 0; i < oscillator_count_; ++i) {
      if (increment_[i] > maximum) maximum = increment_[i];
    }
    return maximum;
  }
  float Next(bool patched = false, float pitch_ratio = 1.0f) {
    float sample = 0.0f;
    for (size_t i = 0; i < oscillator_count_; ++i) {
      phase_[i] += increment_[i] * pitch_ratio;
      phase_[i] -= static_cast<int>(phase_[i]);
      sample += Sine(phase_[i]);
    }
    // Advance phases even while cadence is silent.
    const float cadence = cadence_.Next();
    return gain_ * sample * (patched ? 1.0f : cadence);
  }

 private:
  // Valid oscillator counts are 0 (reset), 1 or 2, so index 2 is never accessed.
  // mutation-equivalent: [3] adds unused phase storage without changing synthesis.
  float phase_[2];
  // mutation-equivalent: [3] adds unused increment storage; the same count bounds every access.
  float increment_[2];
  size_t oscillator_count_;
  float gain_;
  Cadence cadence_;
};

}  // namespace phreak
}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_TONES_H_
