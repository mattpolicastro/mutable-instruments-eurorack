// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#include "phreak_engine.h"

namespace plaits {

void PhreakEngine::Init(stmlib::BufferAllocator* allocator) {
  (void) allocator;
  Reset();
}
void PhreakEngine::Reset() {
  selector_.Reset();
  voices_[0].Reset();
  voices_[1].Reset();
  initialized_ = false;
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
  *already_enveloped = false;
  for (size_t i = 0; i < size; ++i) {
    float sample = voices_[active_voice_].Next();
    if (fade_sample_ < kCrossfadeSamples) {
      const float incoming = voices_[1 - active_voice_].Next();
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
      }
    }
    out[i] = sample;
    aux[i] = out[i];
  }
}

}  // namespace plaits
