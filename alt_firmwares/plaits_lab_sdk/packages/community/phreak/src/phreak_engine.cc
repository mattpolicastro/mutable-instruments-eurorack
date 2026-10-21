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
  voice_.Reset();
}

void PhreakEngine::Render(const EngineParameters& parameters, float* out,
    float* aux, size_t size, bool* already_enveloped) {
  const phreak::TonePlan& plan = phreak::kNorthAmerica;
  const size_t index = selector_.Process(plan, parameters.harmonics);
  voice_.SetTone(plan.entries[index]);
  *already_enveloped = false;
  for (size_t i = 0; i < size; ++i) {
    out[i] = voice_.Next();
    aux[i] = out[i];
  }
}

}  // namespace plaits
