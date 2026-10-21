// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_ARTICULATION_H_
#define PLAITS_LAB_PHREAK_ARTICULATION_H_

#include "plaits/dsp/dsp.h"
#include "plaits/dsp/fx/low_pass_gate.h"

namespace plaits {
namespace phreak {

// One clock per tone voice, advanced once per audio sample, including silence.
// Descriptors use either positive on/off durations or two zeros for sustain.
class Cadence {
 public:
  Cadence() { Reset(); }
  void Reset(float on_seconds = 0.0f, float off_seconds = 0.0f) {
    on_samples_ = static_cast<size_t>(on_seconds * kSampleRate + 0.5f);
    period_samples_ = on_samples_
        + static_cast<size_t>(off_seconds * kSampleRate + 0.5f);
    position_ = 0;
  }

  float Next() {
    // A millisecond spans 48 sample intervals at 48 kHz. The opening is
    // zero at position 0 and unity at 48; the closing reaches zero at the
    // first off sample. Neither ramp extends the descriptor's on window.
    const size_t ramp_end = static_cast<size_t>(0.001f * kSampleRate + 0.5f);
    // mutation-equivalent: At equality both ternary arms return ramp_end.
    size_t ramp_position = position_ < ramp_end ? position_ : ramp_end;
    if (period_samples_) {
      // mutation-equivalent: At equality, else also yields zero via remaining = 0.
      if (position_ >= on_samples_) {
        ramp_position = 0;
      } else {
        const size_t remaining = on_samples_ - position_;
        if (remaining < ramp_position) ramp_position = remaining;
      }
      if (++position_ == period_samples_) position_ = 0;
    // mutation-equivalent: <= parks at 49 instead of 48; both clamp to unity until Reset clears the counter.
    } else if (position_ < ramp_end) {
      // Sustain at unity without an indefinitely growing counter.
      ++position_;
    }
    return static_cast<float>(ramp_position) / ramp_end;
  }

 private:
  size_t on_samples_;
  size_t period_samples_;
  size_t position_;
};

// A single sample clock drives both filters, independently of render blocks.
// The final taper removes filter residue at the fixed keypress deadline.
class Keypress {
 public:
  Keypress() { Reset(); }
  void Reset() {
    position_ = kDuration;
    level_ = attack_start_ = 0.0f;
    main_lpg_.Init();
    aux_lpg_.Init();
  }
  void Trigger() {
    attack_start_ = level_;
    position_ = 0;
  }
  void Process(float* main, float* aux) {
    if (position_ == kDuration) {
      *main = *aux = 0.0f;
      return;
    }
    // mutation-equivalent: At kRelease the quotient is exactly 192/192 = 1.0f, identical to the other arm.
    const float taper = position_ < kRelease ? 1.0f
        : static_cast<float>(kDuration - position_) / (kDuration - kRelease);
    level_ = position_ < kAttack
        ? attack_start_ + (1.0f - attack_start_) * position_ / kAttack
        : taper;
    const float squared = level_ * level_;
    const float cutoff = 0.003f + 0.3f * squared * squared;
    // One-sample calls make gain/cutoff timing independent of host partitioning.
    main_lpg_.Process(level_, cutoff, 0.0f, main, 1);
    aux_lpg_.Process(level_, cutoff, 0.0f, aux, 1);
    *main *= taper;
    *aux *= taper;
    if (++position_ == kDuration) Reset();
  }

 private:
  // Plaits runs at 48 kHz: 1 ms attack, release at 96 ms, idle at 100 ms.
  enum { kAttack = 48, kRelease = 4608, kDuration = 4800 };
  size_t position_;
  float level_;
  float attack_start_;
  LowPassGate main_lpg_;
  LowPassGate aux_lpg_;
};

}  // namespace phreak
}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_ARTICULATION_H_
