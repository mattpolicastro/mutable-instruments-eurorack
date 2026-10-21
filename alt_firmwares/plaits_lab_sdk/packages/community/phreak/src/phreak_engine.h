// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#ifndef PLAITS_LAB_PHREAK_ENGINE_H_
#define PLAITS_LAB_PHREAK_ENGINE_H_

#include "plaits/dsp/engine/engine.h"

namespace plaits {

class PhreakEngine : public Engine {
 public:
  PhreakEngine() : phase_(0.0f) { }
  ~PhreakEngine() { }
  void Init(stmlib::BufferAllocator* allocator);
  void Reset();
  void LoadUserData(const uint8_t* user_data) { (void) user_data; }
  void Render(const EngineParameters& parameters, float* out, float* aux,
      size_t size, bool* already_enveloped);

 private:
  float phase_;
  DISALLOW_COPY_AND_ASSIGN(PhreakEngine);
};

}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_ENGINE_H_
