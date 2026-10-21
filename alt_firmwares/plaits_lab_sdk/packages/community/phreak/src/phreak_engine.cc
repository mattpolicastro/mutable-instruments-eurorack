// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#include "phreak_engine.h"

#include "stmlib/dsp/units.h"

namespace plaits {

void PhreakEngine::Init(stmlib::BufferAllocator* allocator) {
  (void) allocator;
  Reset();
}
void PhreakEngine::Reset() {
  selector_.Reset();
  voices_[0].Reset();
  voices_[1].Reset();
  keypress_.Reset();
  initialized_ = false;
  patched_ = false;
  active_voice_ = 0;
  active_index_ = incoming_index_ = pending_index_ = 0;
  fade_sample_ = kCrossfadeSamples;
}

void PhreakEngine::StartFade(const phreak::TonePlan& plan, size_t index) {
  // Only reuse the silent slot. The outgoing voice keeps its phase/history.
  incoming_index_ = index;
  voices_[1 - active_voice_].Reset();
  voices_[1 - active_voice_].SetTone(plan.entries[index]);
  fade_sample_ = 0;
}

float PhreakEngine::LimitPitchRatio(float ratio) const {
  float maximum = voices_[active_voice_].max_increment();
  if (fade_sample_ < kCrossfadeSamples) {
    const float incoming = voices_[1 - active_voice_].max_increment();
    // Both initialized voices have positive finite maxima, so no signed-zero tie.
    // mutation-equivalent: >= only overwrites maximum with the identical float on a tie.
    if (incoming > maximum) maximum = incoming;
  }
  // One ceiling for every audible component, including both fading voices.
  const float ceiling = 0.45f / maximum;
  // The ceiling is positive and finite; NaN comparisons are false for both operators.
  // mutation-equivalent: <= selects ratio instead of ceiling only when they are identical.
  return ratio < ceiling ? ratio : ceiling;
}

void PhreakEngine::Render(const EngineParameters& parameters, float* out,
    float* aux, size_t size, bool* already_enveloped) {
  const phreak::TonePlan& plan = phreak::kNorthAmerica;
  // Hysteresis follows accepted requests, independently of audible voices.
  // Replacing this single pending target never interrupts an active fade.
  pending_index_ = selector_.Process(plan, parameters.harmonics);
  if (!initialized_) {
    active_index_ = pending_index_;
    voices_[active_voice_].SetTone(plan.entries[active_index_]);
    initialized_ = true;
  } else if (fade_sample_ == kCrossfadeSamples
      && pending_index_ != active_index_) {
    StartFade(plan, pending_index_);
  }
  *already_enveloped = true;
  const bool patched = !(parameters.trigger & TRIGGER_UNPATCHED);
  if (patched != patched_) {
    // Connection flags are authoritative, even after arbitrarily long idle.
    // Discard the old burst/filter history on either connection transition.
    // Patching without an edge therefore closes immediately.
    keypress_.Reset();
    if (!patched) {
      // Restart on phases without resetting oscillators or interrupting a
      // selection fade. Both audible voices need a fresh cadence clock.
      voices_[active_voice_].SetTone(plan.entries[active_index_]);
      if (fade_sample_ < kCrossfadeSamples) {
        voices_[1 - active_voice_].SetTone(plan.entries[incoming_index_]);
      }
    }
    patched_ = patched;
  }
  if (patched && (parameters.trigger & TRIGGER_RISING_EDGE)) {
    // HIGH/LOW alone neither restart nor shorten the keypress deadline.
    keypress_.Trigger();
  }
  const float requested_ratio = stmlib::SemitonesToRatio(parameters.note - 60.0f);
  float pitch_ratio = LimitPitchRatio(requested_ratio);
  for (size_t i = 0; i < size; ++i) {
    float sample = voices_[active_voice_].Next(patched, pitch_ratio);
    if (fade_sample_ < kCrossfadeSamples) {
      const float incoming = voices_[1 - active_voice_].Next(patched, pitch_ratio);
      // Include both endpoints: sample 0 is entirely outgoing and sample 239
      // entirely incoming. Complementary weights keep the mixture bounded.
      const float weight = static_cast<float>(fade_sample_)
          / (kCrossfadeSamples - 1);
      sample = (1.0f - weight) * sample + weight * incoming;
      if (++fade_sample_ == kCrossfadeSamples) {
        active_voice_ = 1 - active_voice_;
        active_index_ = incoming_index_;
        // Begin any queued fade on the very next sample, even within a block.
        if (pending_index_ != active_index_) StartFade(plan, pending_index_);
        // A voice retired or a queued voice began: update the common ceiling
        // immediately so pitch does not depend on the host's block partition.
        pitch_ratio = LimitPitchRatio(requested_ratio);
      }
    }
    // Split after cadence/selection mixing, before any MAIN-only treatment.
    // MAIN is still a bypass until the bad-line stages are implemented.
    // MORPH and macro deliberately do not participate in either path.
    float clean = sample;
    float main = sample;
    // Independent LPG histories share one contour, downstream of the split.
    if (patched) keypress_.Process(&main, &clean);
    out[i] = main;
    aux[i] = clean;
  }
}

}  // namespace plaits
