// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT

#include "phreak_engine.h"

// Placeholder smoke oscillator using the shared sine lookup table.
#include "plaits/dsp/oscillator/sine_oscillator.h"

namespace plaits {

void PhreakEngine::Init(stmlib::BufferAllocator* allocator) {
  (void) allocator;
  Reset();
}
void PhreakEngine::Reset() { phase_ = 0.0f; }

void PhreakEngine::Render(const EngineParameters& parameters, float* out,
    float* aux, size_t size, bool* already_enveloped) {
  const float frequency = NoteToFrequency(parameters.note);
  *already_enveloped = false;
  for (size_t i = 0; i < size; ++i) {
    phase_ += frequency;
    phase_ -= static_cast<int>(phase_);
    out[i] = 0.5f * Sine(phase_);   // sine LUT — phase in [0, 1)
    aux[i] = out[i];
  }
}

}  // namespace plaits
