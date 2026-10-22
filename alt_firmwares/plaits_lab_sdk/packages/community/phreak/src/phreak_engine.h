// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_ENGINE_H_
#define PLAITS_LAB_PHREAK_ENGINE_H_

#include "plaits/dsp/engine/engine.h"
#include "phreak_bad_line.h"
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
  void StartFade(const phreak::ToneEntry* entry);
  float LimitPitchRatio(float ratio) const;

  phreak::ToneSelector system_selector_;
  phreak::ToneSelector selector_;
  phreak::ToneVoice voices_[2];
  phreak::Keypress keypress_;
  phreak::BadLine bad_line_;
  bool initialized_;
  bool patched_;
  size_t system_;
  size_t active_voice_;
  const phreak::ToneEntry* active_entry_;
  const phreak::ToneEntry* incoming_entry_;
  const phreak::ToneEntry* pending_entry_;
  // kCrossfadeSamples means idle; otherwise this is the next fade sample.
  size_t fade_sample_;
  DISALLOW_COPY_AND_ASSIGN(PhreakEngine);
};

}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_ENGINE_H_
