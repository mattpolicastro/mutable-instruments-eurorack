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

// Signed, zero-centred grid; rounding ties go away from zero.
inline float Quantize(float sample, int bits) {
  CONSTRAIN(sample, -1.0f, 1.0f);
  const float scale = static_cast<float>((1 << bits) - 1);
  const float magnitude = sample < 0.0f ? -sample : sample;
  const int level = static_cast<int>(magnitude * (0.5f * scale) + 0.5f);
  float quantized = level * (2.0f / scale);
  if (quantized > 1.0f) quantized = 1.0f;
  return sample < 0.0f ? -quantized : quantized;
}

// MAIN-only telephone band, drive and reduction. Cutoffs do not track pitch.
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
    // mutation-equivalent: 0 -> 1 adds only a zero-step, zero-target update; SetTimbre replaces the counter if the target changes.
    remaining_ = 0;
    saturation_mix_ = saturation_target_ = saturation_start_ = saturation_step_ = 0.0f;
    saturation_remaining_ = 0;
    reduction_mix_ = reduction_target_ = reduction_start_ = reduction_step_ = 0.0f;
    // mutation-equivalent: 0 -> 1 snaps the already-zero mix to its zero target; SetTimbre replaces the counter if the target changes.
    reduction_remaining_ = 0;
    held_ = 0.0f;
    hold_remaining_ = 0;
    hold_length_ = 1;
    bits_ = 12;
  }

  // Clean at noon, with a small dead zone for knob jitter. Counter-clockwise
  // is an analog line (telephone band, then saturation); clockwise a digital
  // one (telephone band, then bit and sample-rate reduction).
  void SetTimbre(float timbre) {
    CONSTRAIN(timbre, 0.0f, 1.0f);
    const float kDeadZone = 0.02f;
    float analog = (0.5f - kDeadZone - timbre) / (0.5f - kDeadZone);
    float digital = (timbre - 0.5f - kDeadZone) / (0.5f - kDeadZone);
    CONSTRAIN(analog, 0.0f, 1.0f);
    CONSTRAIN(digital, 0.0f, 1.0f);
    float target = analog > 0.0f ? 2.0f * analog : 3.0f * digital;
    CONSTRAIN(target, 0.0f, 1.0f);
    if (target != target_mix_) {
      target_mix_ = target;
      remaining_ = kTransitionSamples;
      mix_step_ = (target_mix_ - mix_) / kTransitionSamples;
    }
    float saturation = 2.0f * analog - 1.0f;
    CONSTRAIN(saturation, 0.0f, 1.0f);
    if (saturation != saturation_target_) {
      saturation_target_ = saturation;
      saturation_start_ = saturation_mix_;
      saturation_remaining_ = kTransitionSamples;
      saturation_step_ = (saturation_target_ - saturation_mix_)
          / kTransitionSamples;
    }
    float reduction = (3.0f * digital - 1.0f) / 2.0f;
    CONSTRAIN(reduction, 0.0f, 1.0f);
    if (reduction != reduction_target_) {
      reduction_target_ = reduction;
      reduction_start_ = reduction_mix_;
      reduction_remaining_ = kTransitionSamples;
      reduction_step_ = (reduction_target_ - reduction_mix_)
          / kTransitionSamples;
      // Resolution steps are intentional; only the wet mix is smoothed.
      const int resolution = static_cast<int>(7.0f * reduction);
      bits_ = 12 - resolution;
      const size_t length = 1 + resolution;
      if (length != hold_length_) {
        hold_length_ = length;
        hold_remaining_ = 0;
      }
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
    if (reduction_remaining_) {
      --reduction_remaining_;
      reduction_mix_ = reduction_remaining_ == 0 ? reduction_target_
          : reduction_start_ + reduction_step_
              * (kTransitionSamples - reduction_remaining_);
    }
    // Exact endpoint branches also avoid roundoff from dry/wet cancellation.
    const float filtered = mix_ == 0.0f ? dry : mix_ == 1.0f ? wet
        : dry + mix_ * (wet - dry);
    // Deriving drive from the smoothed mix makes both follow the same 5 ms
    // linear ramp, including retargets before the previous ramp has finished.
    float saturated = filtered;
    if (saturation_mix_ != 0.0f) {
      const float wet_saturation = SoftSaturate(
          filtered, 1.0f + 7.0f * saturation_mix_);
      saturated = saturation_mix_ == 1.0f ? wet_saturation
          : filtered + saturation_mix_ * (wet_saturation - filtered);
    }
    if (reduction_mix_ == 0.0f) {
      // No held history can leak into the clean or saturation-only endpoints.
      hold_remaining_ = 0;
      held_ = 0.0f;
      return saturated;
    }
    if (hold_remaining_ == 0) {
      held_ = Quantize(saturated, bits_);
      hold_remaining_ = hold_length_;
    }
    --hold_remaining_;
    // Return the grid value directly at full wet, without cancellation error.
    return reduction_mix_ == 1.0f ? held_
        : saturated + reduction_mix_ * (held_ - saturated);
  }

 private:
  // mutation-equivalent: 48 -> 49 changes only the comment; compiled timing still uses 240 samples.
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
  float reduction_mix_;
  float reduction_target_;
  float reduction_start_;
  float reduction_step_;
  size_t reduction_remaining_;
  float held_;
  size_t hold_remaining_;
  size_t hold_length_;
  int bits_;
};

}  // namespace phreak
}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_BAD_LINE_H_
