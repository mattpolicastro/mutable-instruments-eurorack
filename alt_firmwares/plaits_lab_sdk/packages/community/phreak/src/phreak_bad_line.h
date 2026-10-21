// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_BAD_LINE_H_
#define PLAITS_LAB_PHREAK_BAD_LINE_H_

#include "plaits/dsp/dsp.h"
#include "stmlib/dsp/filter.h"

namespace plaits {
namespace phreak {

// MAIN-only telephone band. Cutoffs stay fixed as the tone pitch changes.
class BadLine {
 public:
  BadLine() { Reset(); }
  void Reset() {
    high_pass_.Reset();
    low_pass_.Reset();
    high_pass_.set_f_q<stmlib::FREQUENCY_ACCURATE>(
        300.0f / kSampleRate, 0.70710678f);
    low_pass_.set_f_q<stmlib::FREQUENCY_ACCURATE>(
        3400.0f / kSampleRate, 0.70710678f);
    mix_ = target_mix_ = mix_step_ = 0.0f;
    remaining_ = 0;
  }

  void SetTimbre(float timbre) {
    CONSTRAIN(timbre, 0.0f, 1.0f);
    const float target = timbre < 1.0f / 3.0f ? 3.0f * timbre : 1.0f;
    if (target != target_mix_) {
      target_mix_ = target;
      remaining_ = kTransitionSamples;
      mix_step_ = (target_mix_ - mix_) / kTransitionSamples;
    }
  }

  float Process(float dry) {
    // Keep the filters warm even in bypass, without feeding their history
    // into the clean endpoint. Repeated control blocks do not restart ramps.
    const float high = high_pass_.Process<stmlib::FILTER_MODE_HIGH_PASS>(dry);
    const float wet = low_pass_.Process<stmlib::FILTER_MODE_LOW_PASS>(high);
    if (remaining_) {
      mix_ += mix_step_;
      if (--remaining_ == 0) mix_ = target_mix_;
    }
    // Exact endpoint branches also avoid roundoff from dry/wet cancellation.
    if (mix_ == 0.0f) return dry;
    if (mix_ == 1.0f) return wet;
    return dry + mix_ * (wet - dry);
  }

 private:
  enum { kTransitionSamples = 240 };  // 5 ms at Plaits' 48 kHz sample rate.
  stmlib::Svf high_pass_;
  stmlib::Svf low_pass_;
  float mix_;
  float target_mix_;
  float mix_step_;
  size_t remaining_;
};

}  // namespace phreak
}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_BAD_LINE_H_
