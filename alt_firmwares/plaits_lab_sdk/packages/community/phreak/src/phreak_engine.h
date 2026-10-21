// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_ENGINE_H_
#define PLAITS_LAB_PHREAK_ENGINE_H_

#include "plaits/dsp/engine/engine.h"
#include "phreak_tones.h"

namespace plaits {

class PhreakEngine : public Engine {
 public:
  PhreakEngine() { }
  ~PhreakEngine() { }
  void Init(stmlib::BufferAllocator* allocator);
  void Reset();
  void LoadUserData(const uint8_t* user_data) { (void) user_data; }
  void Render(const EngineParameters& parameters, float* out, float* aux,
      size_t size, bool* already_enveloped);

 private:
  enum { kCrossfadeSamples = 240 };
  void StartFade(const phreak::TonePlan& plan, size_t index);

  phreak::ToneSelector selector_;
  phreak::ToneVoice voices_[2];
  phreak::Keypress keypress_;
  bool initialized_;
  size_t active_voice_;
  size_t active_index_;
  size_t incoming_index_;
  size_t pending_index_;
  // kCrossfadeSamples means idle; otherwise this is the next fade sample.
  size_t fade_sample_;
  DISALLOW_COPY_AND_ASSIGN(PhreakEngine);
};

}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_ENGINE_H_
