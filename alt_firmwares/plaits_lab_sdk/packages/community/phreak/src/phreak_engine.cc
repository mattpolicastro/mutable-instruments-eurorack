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
  system_selector_.Reset();
  selector_.Reset();
  voices_[0].Reset();
  voices_[1].Reset();
  keypress_.Reset();
  bad_line_.Reset();
  initialized_ = false;
  patched_ = false;
  system_ = 0;
  active_voice_ = 0;
  active_entry_ = incoming_entry_ = pending_entry_ = &phreak::kNorthAmerica.entries[0];
  fade_sample_ = kCrossfadeSamples;
}

void PhreakEngine::StartFade(const phreak::ToneEntry* entry) {
  // Only reuse the silent slot. The outgoing voice keeps its phase/history.
  incoming_entry_ = entry;
  voices_[1 - active_voice_].Reset();
  voices_[1 - active_voice_].SetTone(*entry);
  fade_sample_ = 0;
}

float PhreakEngine::LimitPitchRatio(float ratio) const {
  float maximum = voices_[active_voice_].max_increment();
  if (fade_sample_ < kCrossfadeSamples) {
    const float incoming = voices_[1 - active_voice_].max_increment();
    if (incoming > maximum) maximum = incoming;
  }
  // One ceiling for every audible component, including both fading voices.
  const float ceiling = 0.45f / maximum;
  return ratio < ceiling ? ratio : ceiling;
}

void PhreakEngine::Render(const EngineParameters& parameters, float* out,
    float* aux, size_t size, bool* already_enveloped) {
  // HARMONICS selects the tone system, MORPH a tone within it. A new system
  // re-acquires MORPH's zone in its own table; the change crossfades as usual.
  const size_t system = system_selector_.Process(phreak::kNumPlans, parameters.harmonics);
  if (!initialized_ || system != system_) {
    system_ = system;
    selector_.Reset();
  }
  const phreak::TonePlan& plan = *phreak::kPlans[system_];
  pending_entry_ = &plan.entries[selector_.Process(plan, parameters.morph)];
  if (!initialized_) {
    active_entry_ = pending_entry_;
    voices_[active_voice_].SetTone(*active_entry_);
    initialized_ = true;
  } else if (fade_sample_ == kCrossfadeSamples
      && pending_entry_ != active_entry_) {
    StartFade(pending_entry_);
  }
  voices_[0].set_twist(parameters.macro);
  voices_[1].set_twist(parameters.macro);
  *already_enveloped = true;
  const bool patched = !(parameters.trigger & TRIGGER_UNPATCHED);
  if (patched != patched_) {
    keypress_.Reset();
    if (!patched) {
      voices_[active_voice_].SetTone(*active_entry_);
      if (fade_sample_ < kCrossfadeSamples) {
        voices_[1 - active_voice_].SetTone(*incoming_entry_);
      }
    }
    patched_ = patched;
  }
  if (patched && (parameters.trigger & TRIGGER_RISING_EDGE)) {
    // A keypress plays the entry from its first step.
    keypress_.Trigger();
    voices_[active_voice_].SetTone(*active_entry_);
    if (fade_sample_ < kCrossfadeSamples) {
      voices_[1 - active_voice_].SetTone(*incoming_entry_);
    }
  }
  const float requested_ratio = stmlib::SemitonesToRatio(parameters.note - 60.0f);
  float pitch_ratio = LimitPitchRatio(requested_ratio);
  bad_line_.SetTimbre(parameters.timbre);
  for (size_t i = 0; i < size; ++i) {
    float sample = voices_[active_voice_].Next(pitch_ratio);
    if (fade_sample_ < kCrossfadeSamples) {
      const float incoming = voices_[1 - active_voice_].Next(pitch_ratio);
      const float weight = static_cast<float>(fade_sample_)
          / (kCrossfadeSamples - 1);
      sample = (1.0f - weight) * sample + weight * incoming;
      if (++fade_sample_ == kCrossfadeSamples) {
        active_voice_ = 1 - active_voice_;
        active_entry_ = incoming_entry_;
        if (pending_entry_ != active_entry_) StartFade(pending_entry_);
        pitch_ratio = LimitPitchRatio(requested_ratio);
      }
    }
    float clean = sample;
    float main = bad_line_.Process(sample);
    if (patched) keypress_.Process(&main, &clean);
    out[i] = main;
    aux[i] = clean;
  }
}

}  // namespace plaits
