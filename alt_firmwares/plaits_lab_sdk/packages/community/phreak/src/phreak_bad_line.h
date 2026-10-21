// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_BAD_LINE_H_
#define PLAITS_LAB_PHREAK_BAD_LINE_H_

#include "plaits/dsp/dsp.h"
#include "stmlib/dsp/filter.h"

namespace plaits {
namespace phreak {

// Bounded odd soft curve. Drive is in [1, 8] in the bad-line path.
inline float SoftSaturate(float sample, float drive) {
  const float driven = drive * sample;
  const float magnitude = driven < 0.0f ? -driven : driven;
  return 0.8f * driven / (1.0f + magnitude);
}

// MAIN-only telephone band and drive. Cutoffs stay fixed as pitch changes.
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
    saturation_mix_ = saturation_target_ = saturation_start_ = saturation_step_ = 0.0f;
    saturation_remaining_ = 0;
  }

  void SetTimbre(float timbre) {
    CONSTRAIN(timbre, 0.0f, 1.0f);
    const float target = timbre < 1.0f / 3.0f ? 3.0f * timbre : 1.0f;
    if (target != target_mix_) {
      target_mix_ = target;
      remaining_ = kTransitionSamples;
      mix_step_ = (target_mix_ - mix_) / kTransitionSamples;
    }
    float saturation = 3.0f * timbre - 1.0f;
    CONSTRAIN(saturation, 0.0f, 1.0f);
    if (saturation != saturation_target_) {
      saturation_target_ = saturation;
      saturation_start_ = saturation_mix_;
      saturation_remaining_ = kTransitionSamples;
      saturation_step_ = (saturation_target_ - saturation_mix_)
          / kTransitionSamples;
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
    if (saturation_remaining_) {
      --saturation_remaining_;
      // Interpolate from the ramp start to avoid accumulating float error.
      saturation_mix_ = saturation_remaining_ == 0 ? saturation_target_
          : saturation_start_ + saturation_step_
              * (kTransitionSamples - saturation_remaining_);
    }
    // Exact endpoint branches also avoid roundoff from dry/wet cancellation.
    const float filtered = mix_ == 0.0f ? dry : mix_ == 1.0f ? wet
        : dry + mix_ * (wet - dry);
    if (saturation_mix_ == 0.0f) return filtered;
    // Deriving drive from the smoothed mix makes both follow the same 5 ms
    // linear ramp, including retargets before the previous ramp has finished.
    const float saturated = SoftSaturate(filtered, 1.0f + 7.0f * saturation_mix_);
    if (saturation_mix_ == 1.0f) return saturated;
    return filtered + saturation_mix_ * (saturated - filtered);
  }

 private:
  enum { kTransitionSamples = 240 };  // 5 ms at Plaits' 48 kHz sample rate.
  stmlib::Svf high_pass_;
  stmlib::Svf low_pass_;
  float mix_;
  float target_mix_;
  float mix_step_;
  size_t remaining_;
  float saturation_mix_;
  float saturation_target_;
  float saturation_start_;
  float saturation_step_;
  size_t saturation_remaining_;
};

}  // namespace phreak
}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_BAD_LINE_H_
