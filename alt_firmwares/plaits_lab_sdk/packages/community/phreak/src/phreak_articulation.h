// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_ARTICULATION_H_
#define PLAITS_LAB_PHREAK_ARTICULATION_H_

#include "plaits/dsp/dsp.h"

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
    size_t ramp_position = position_ < ramp_end ? position_ : ramp_end;
    if (period_samples_) {
      if (position_ >= on_samples_) {
        ramp_position = 0;
      } else {
        const size_t remaining = on_samples_ - position_;
        if (remaining < ramp_position) ramp_position = remaining;
      }
      if (++position_ == period_samples_) position_ = 0;
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

}  // namespace phreak
}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_ARTICULATION_H_
