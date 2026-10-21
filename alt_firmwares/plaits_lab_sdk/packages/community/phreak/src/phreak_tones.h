// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT
//
// v2 prototype: every table entry is a list of timed steps, and each step is
// one kind of signal. Steps loop; a step of 0 seconds holds forever.

#ifndef PLAITS_LAB_PHREAK_TONES_H_
#define PLAITS_LAB_PHREAK_TONES_H_

#include "plaits/dsp/dsp.h"
#include "plaits/dsp/oscillator/sine_oscillator.h"
#include "phreak_articulation.h"

namespace plaits {
namespace phreak {

enum Signal {
  SIGNAL_SILENCE,
  SIGNAL_TONES,      // up to four sines at hz[]
  SIGNAL_FSK,        // random bits at rate baud: hz[0] mark (1), hz[1] space (0)
  SIGNAL_DPSK,       // carrier hz[0], four-phase differential symbols at rate baud
  SIGNAL_QAM,        // carrier hz[0], random constellation points at rate baud
  SIGNAL_ANSAM,      // hz[0] with 15 Hz AM and a phase reversal every 450 ms
  SIGNAL_MULTITONE,  // every multiple of hz[0] up to hz[1], except hz[2] and hz[3] multiples
};

struct Step {
  float seconds;
  int signal;
  float hz[4];
  float rate;
};

struct ToneEntry {
  const char* label;
  const Step* steps;
  size_t num_steps;
};

struct TonePlan {
  const char* locale;
  const ToneEntry* entries;
  size_t count;
};

#define PHREAK_TONES(s, a, b, c, d) { s, SIGNAL_TONES, { a, b, c, d }, 0.0f }
#define PHREAK_T1(s, a) PHREAK_TONES(s, a, 0.0f, 0.0f, 0.0f)
#define PHREAK_T2(s, a, b) PHREAK_TONES(s, a, b, 0.0f, 0.0f)
#define PHREAK_OFF(s) { s, SIGNAL_SILENCE, { 0.0f, 0.0f, 0.0f, 0.0f }, 0.0f }
#define PHREAK_FSK(s, mark, space, baud) { s, SIGNAL_FSK, { mark, space, 0.0f, 0.0f }, baud }
#define PHREAK_DPSK(s, carrier, baud) { s, SIGNAL_DPSK, { carrier, 0.0f, 0.0f, 0.0f }, baud }
#define PHREAK_QAM(s, carrier, baud) { s, SIGNAL_QAM, { carrier, 0.0f, 0.0f, 0.0f }, baud }
#define PHREAK_ANSAM(s) { s, SIGNAL_ANSAM, { 2100.0f, 0.0f, 0.0f, 0.0f }, 15.0f }
#define PHREAK_PROBE(s) { s, SIGNAL_MULTITONE, { 150.0f, 3750.0f, 900.0f, 1200.0f }, 0.0f }
#define PHREAK_STEPS(array) array, sizeof(array) / sizeof(array[0])
#define PHREAK_ENTRIES(array) array, sizeof(array) / sizeof(array[0])

// --- North America (v1's table, unchanged) ----------------------------------

const Step kNaDial[] = { PHREAK_T2(0.0f, 350.0f, 440.0f) };
const Step kNaKey1[] = { PHREAK_T2(0.0f, 697.0f, 1209.0f) };
const Step kNaKey2[] = { PHREAK_T2(0.0f, 697.0f, 1336.0f) };
const Step kNaKey3[] = { PHREAK_T2(0.0f, 697.0f, 1477.0f) };
const Step kNaKey4[] = { PHREAK_T2(0.0f, 770.0f, 1209.0f) };
const Step kNaKey5[] = { PHREAK_T2(0.0f, 770.0f, 1336.0f) };
const Step kNaKey6[] = { PHREAK_T2(0.0f, 770.0f, 1477.0f) };
const Step kNaKey7[] = { PHREAK_T2(0.0f, 852.0f, 1209.0f) };
const Step kNaKey8[] = { PHREAK_T2(0.0f, 852.0f, 1336.0f) };
const Step kNaKey9[] = { PHREAK_T2(0.0f, 852.0f, 1477.0f) };
const Step kNaKey0[] = { PHREAK_T2(0.0f, 941.0f, 1336.0f) };
const Step kNaHash[] = { PHREAK_T2(0.0f, 941.0f, 1477.0f) };
const Step kNaStar[] = { PHREAK_T2(0.0f, 941.0f, 1209.0f) };
const Step kNaBusy[] = { PHREAK_T2(0.5f, 480.0f, 620.0f), PHREAK_OFF(0.5f) };
const Step kNaRing[] = { PHREAK_T2(2.0f, 440.0f, 480.0f), PHREAK_OFF(4.0f) };
const Step kNaKeyA[] = { PHREAK_T2(0.0f, 697.0f, 1633.0f) };
const Step kNaKeyB[] = { PHREAK_T2(0.0f, 770.0f, 1633.0f) };
const Step kNaKeyC[] = { PHREAK_T2(0.0f, 852.0f, 1633.0f) };
const Step kNaKeyD[] = { PHREAK_T2(0.0f, 941.0f, 1633.0f) };
const Step kNaFskSpace[] = { PHREAK_T1(0.0f, 2200.0f) };
const Step kNaFskMark[] = { PHREAK_T1(0.0f, 1200.0f) };

const ToneEntry kNorthAmericanEntries[] = {
  { "dial", PHREAK_STEPS(kNaDial) }, { "key-1", PHREAK_STEPS(kNaKey1) },
  { "key-2", PHREAK_STEPS(kNaKey2) }, { "key-3", PHREAK_STEPS(kNaKey3) },
  { "key-4", PHREAK_STEPS(kNaKey4) }, { "key-5", PHREAK_STEPS(kNaKey5) },
  { "key-6", PHREAK_STEPS(kNaKey6) }, { "key-7", PHREAK_STEPS(kNaKey7) },
  { "key-8", PHREAK_STEPS(kNaKey8) }, { "key-9", PHREAK_STEPS(kNaKey9) },
  { "key-0", PHREAK_STEPS(kNaKey0) }, { "hash", PHREAK_STEPS(kNaHash) },
  { "star", PHREAK_STEPS(kNaStar) }, { "busy", PHREAK_STEPS(kNaBusy) },
  { "ring", PHREAK_STEPS(kNaRing) }, { "key-a", PHREAK_STEPS(kNaKeyA) },
  { "key-b", PHREAK_STEPS(kNaKeyB) }, { "key-c", PHREAK_STEPS(kNaKeyC) },
  { "key-d", PHREAK_STEPS(kNaKeyD) }, { "fsk-space", PHREAK_STEPS(kNaFskSpace) },
  { "fsk-mark", PHREAK_STEPS(kNaFskMark) }
};

// --- United Kingdom (BT) ---------------------------------------------------

const Step kUkDial[] = { PHREAK_T2(0.0f, 350.0f, 450.0f) };
const Step kUkRing[] = {
  PHREAK_T2(0.4f, 400.0f, 450.0f), PHREAK_OFF(0.2f),
  PHREAK_T2(0.4f, 400.0f, 450.0f), PHREAK_OFF(2.0f)
};
const Step kUkEngaged[] = { PHREAK_T1(0.375f, 400.0f), PHREAK_OFF(0.375f) };
const Step kUkCongestion[] = {
  PHREAK_T1(0.4f, 400.0f), PHREAK_OFF(0.35f),
  PHREAK_T1(0.225f, 400.0f), PHREAK_OFF(0.525f)
};
const Step kUkUnobtainable[] = { PHREAK_T1(0.0f, 400.0f) };

const ToneEntry kUkEntries[] = {
  { "dial", PHREAK_STEPS(kUkDial) }, { "ring", PHREAK_STEPS(kUkRing) },
  { "engaged", PHREAK_STEPS(kUkEngaged) },
  { "congestion", PHREAK_STEPS(kUkCongestion) },
  { "unobtainable", PHREAK_STEPS(kUkUnobtainable) }
};

// --- Europe (CEPT 425 Hz) --------------------------------------------------

const Step kEuDial[] = { PHREAK_T1(0.0f, 425.0f) };
const Step kEuRing[] = { PHREAK_T1(1.0f, 425.0f), PHREAK_OFF(4.0f) };
const Step kEuBusy[] = { PHREAK_T1(0.5f, 425.0f), PHREAK_OFF(0.5f) };
const Step kEuCongestion[] = { PHREAK_T1(0.25f, 425.0f), PHREAK_OFF(0.25f) };

const ToneEntry kEuropeEntries[] = {
  { "dial", PHREAK_STEPS(kEuDial) }, { "ring", PHREAK_STEPS(kEuRing) },
  { "busy", PHREAK_STEPS(kEuBusy) }, { "congestion", PHREAK_STEPS(kEuCongestion) }
};

// --- Japan (NTT): ringback is 400 Hz warbled at 16 Hz, as a beating pair ----

const Step kJpDial[] = { PHREAK_T1(0.0f, 400.0f) };
const Step kJpRing[] = { PHREAK_T2(1.0f, 392.0f, 408.0f), PHREAK_OFF(2.0f) };
const Step kJpBusy[] = { PHREAK_T1(0.5f, 400.0f), PHREAK_OFF(0.5f) };

const ToneEntry kJapanEntries[] = {
  { "dial", PHREAK_STEPS(kJpDial) }, { "ring", PHREAK_STEPS(kJpRing) },
  { "busy", PHREAK_STEPS(kJpBusy) }
};

// --- Blue box: Bell System R1 MF, in a call's order -----------------------

const Step kBbSeize[] = { PHREAK_T1(0.0f, 2600.0f) };
const Step kBbKp[] = { PHREAK_T2(0.0f, 1100.0f, 1700.0f) };
const Step kBb1[] = { PHREAK_T2(0.0f, 700.0f, 900.0f) };
const Step kBb2[] = { PHREAK_T2(0.0f, 700.0f, 1100.0f) };
const Step kBb3[] = { PHREAK_T2(0.0f, 900.0f, 1100.0f) };
const Step kBb4[] = { PHREAK_T2(0.0f, 700.0f, 1300.0f) };
const Step kBb5[] = { PHREAK_T2(0.0f, 900.0f, 1300.0f) };
const Step kBb6[] = { PHREAK_T2(0.0f, 1100.0f, 1300.0f) };
const Step kBb7[] = { PHREAK_T2(0.0f, 700.0f, 1500.0f) };
const Step kBb8[] = { PHREAK_T2(0.0f, 900.0f, 1500.0f) };
const Step kBb9[] = { PHREAK_T2(0.0f, 1100.0f, 1500.0f) };
const Step kBb0[] = { PHREAK_T2(0.0f, 1300.0f, 1500.0f) };
const Step kBbSt[] = { PHREAK_T2(0.0f, 1500.0f, 1700.0f) };

const ToneEntry kBlueBoxEntries[] = {
  { "seize", PHREAK_STEPS(kBbSeize) }, { "kp", PHREAK_STEPS(kBbKp) },
  { "mf-1", PHREAK_STEPS(kBb1) }, { "mf-2", PHREAK_STEPS(kBb2) },
  { "mf-3", PHREAK_STEPS(kBb3) }, { "mf-4", PHREAK_STEPS(kBb4) },
  { "mf-5", PHREAK_STEPS(kBb5) }, { "mf-6", PHREAK_STEPS(kBb6) },
  { "mf-7", PHREAK_STEPS(kBb7) }, { "mf-8", PHREAK_STEPS(kBb8) },
  { "mf-9", PHREAK_STEPS(kBb9) }, { "mf-0", PHREAK_STEPS(kBb0) },
  { "st", PHREAK_STEPS(kBbSt) }
};

// --- Specials: red box coins, intercepts, howler, test tone ---------------

#define PHREAK_COIN(s) PHREAK_T2(s, 1700.0f, 2200.0f)
const Step kRedNickel[] = { PHREAK_COIN(0.066f), PHREAK_OFF(0.934f) };
const Step kRedDime[] = {
  PHREAK_COIN(0.066f), PHREAK_OFF(0.066f), PHREAK_COIN(0.066f), PHREAK_OFF(0.802f)
};
const Step kRedQuarter[] = {
  PHREAK_COIN(0.033f), PHREAK_OFF(0.033f), PHREAK_COIN(0.033f), PHREAK_OFF(0.033f),
  PHREAK_COIN(0.033f), PHREAK_OFF(0.033f), PHREAK_COIN(0.033f), PHREAK_OFF(0.033f),
  PHREAK_COIN(0.033f), PHREAK_OFF(0.67f)
};
const Step kSitIntercept[] = {
  PHREAK_T1(0.274f, 913.8f), PHREAK_T1(0.274f, 1370.6f), PHREAK_T1(0.380f, 1776.7f),
  PHREAK_OFF(2.0f)
};
const Step kSitNoCircuit[] = {
  PHREAK_T1(0.380f, 985.2f), PHREAK_T1(0.380f, 1428.5f), PHREAK_T1(0.380f, 1776.7f),
  PHREAK_OFF(2.0f)
};
const Step kHowler[] = {
  PHREAK_TONES(0.1f, 1400.0f, 2060.0f, 2450.0f, 2600.0f), PHREAK_OFF(0.1f)
};
const Step kTestTone[] = { PHREAK_T1(0.0f, 1004.0f) };

const ToneEntry kSpecialEntries[] = {
  { "red-box-nickel", PHREAK_STEPS(kRedNickel) },
  { "red-box-dime", PHREAK_STEPS(kRedDime) },
  { "red-box-quarter", PHREAK_STEPS(kRedQuarter) },
  { "sit-intercept", PHREAK_STEPS(kSitIntercept) },
  { "sit-no-circuit", PHREAK_STEPS(kSitNoCircuit) },
  { "off-hook-howler", PHREAK_STEPS(kHowler) },
  { "test-1004", PHREAK_STEPS(kTestTone) }
};

// --- Modem ----------------------------------------------------------------

const Step kAnsam[] = { PHREAK_ANSAM(0.0f) };
const Step kBell103Orig[] = { PHREAK_FSK(0.0f, 1270.0f, 1070.0f, 300.0f) };
const Step kBell103Ans[] = { PHREAK_FSK(0.0f, 2225.0f, 2025.0f, 300.0f) };
const Step kV21Ch1[] = { PHREAK_FSK(0.0f, 980.0f, 1180.0f, 300.0f) };
const Step kV21Ch2[] = { PHREAK_FSK(0.0f, 1650.0f, 1850.0f, 300.0f) };
const Step kBell202[] = { PHREAK_FSK(0.0f, 1200.0f, 2200.0f, 1200.0f) };
const Step kCallerId[] = {
  PHREAK_T2(2.0f, 440.0f, 480.0f), PHREAK_OFF(0.5f),
  PHREAK_FSK(0.5f, 1200.0f, 2200.0f, 1200.0f), PHREAK_OFF(3.0f)
};
const Step kV22Orig[] = { PHREAK_DPSK(0.0f, 1200.0f, 600.0f) };
const Step kV22Ans[] = { PHREAK_DPSK(0.0f, 2400.0f, 600.0f) };
const Step kV34Probe[] = { PHREAK_PROBE(0.0f) };
const Step kTraining[] = { PHREAK_QAM(0.0f, 1800.0f, 2400.0f) };
// Dial-up connect: dial tone, 555-0123, ringback, answer, V.8 exchange, line
// probing, training, then the speaker mutes.
#define PHREAK_DIGIT(a, b) PHREAK_T2(0.09f, a, b), PHREAK_OFF(0.07f)
const Step kConnect[] = {
  PHREAK_T2(1.0f, 350.0f, 440.0f), PHREAK_OFF(0.3f),
  PHREAK_DIGIT(770.0f, 1336.0f), PHREAK_DIGIT(770.0f, 1336.0f),
  PHREAK_DIGIT(770.0f, 1336.0f), PHREAK_DIGIT(941.0f, 1336.0f),
  PHREAK_DIGIT(697.0f, 1209.0f), PHREAK_DIGIT(697.0f, 1336.0f),
  PHREAK_DIGIT(697.0f, 1477.0f),
  PHREAK_OFF(1.2f), PHREAK_T2(2.0f, 440.0f, 480.0f), PHREAK_OFF(0.6f),
  PHREAK_ANSAM(2.4f),
  PHREAK_FSK(0.45f, 980.0f, 1180.0f, 300.0f),
  PHREAK_FSK(0.45f, 1650.0f, 1850.0f, 300.0f), PHREAK_OFF(0.1f),
  PHREAK_PROBE(0.3f), PHREAK_OFF(0.05f), PHREAK_PROBE(0.3f), PHREAK_OFF(0.1f),
  PHREAK_DPSK(0.4f, 1200.0f, 600.0f),
  PHREAK_QAM(2.6f, 1800.0f, 2400.0f),
  PHREAK_OFF(0.0f)
};

const ToneEntry kModemEntries[] = {
  { "answer", PHREAK_STEPS(kAnsam) },
  { "bell-103-originate", PHREAK_STEPS(kBell103Orig) },
  { "bell-103-answer", PHREAK_STEPS(kBell103Ans) },
  { "v21-channel-1", PHREAK_STEPS(kV21Ch1) },
  { "v21-channel-2", PHREAK_STEPS(kV21Ch2) },
  { "bell-202", PHREAK_STEPS(kBell202) },
  { "caller-id", PHREAK_STEPS(kCallerId) },
  { "v22-originate", PHREAK_STEPS(kV22Orig) },
  { "v22-answer", PHREAK_STEPS(kV22Ans) },
  { "v34-probe", PHREAK_STEPS(kV34Probe) },
  { "training", PHREAK_STEPS(kTraining) },
  { "connect", PHREAK_STEPS(kConnect) }
};

const TonePlan kNorthAmerica = { "north-america", PHREAK_ENTRIES(kNorthAmericanEntries) };
const TonePlan kUnitedKingdom = { "united-kingdom", PHREAK_ENTRIES(kUkEntries) };
const TonePlan kEurope = { "europe", PHREAK_ENTRIES(kEuropeEntries) };
const TonePlan kJapan = { "japan", PHREAK_ENTRIES(kJapanEntries) };
const TonePlan kBlueBox = { "blue-box", PHREAK_ENTRIES(kBlueBoxEntries) };
const TonePlan kSpecials = { "specials", PHREAK_ENTRIES(kSpecialEntries) };
const TonePlan kModem = { "modem", PHREAK_ENTRIES(kModemEntries) };

// HARMONICS selects one of these systems; MORPH an entry within it.
const TonePlan* const kPlans[] = {
  &kNorthAmerica, &kUnitedKingdom, &kEurope, &kJapan, &kBlueBox, &kSpecials, &kModem
};
const size_t kNumPlans = sizeof(kPlans) / sizeof(kPlans[0]);

// Counts must be nonzero. Positive integer conversion implements floor.
inline size_t NominalIndex(size_t count, float value) {
  if (!(value > 0.0f)) return 0;
  if (value >= 1.0f) return count - 1;
  const size_t index = static_cast<size_t>(value * count);
  return index < count ? index : count - 1;
}

inline size_t NominalToneIndex(const TonePlan& plan, float value) {
  return NominalIndex(plan.count, value);
}

// Retain the latest accepted request independently of oscillator state.
class ToneSelector {
 public:
  ToneSelector() { Reset(); }
  void Reset() {
    initialized_ = false;
    index_ = 0;
  }
  size_t Process(const TonePlan& plan, float value) {
    return Process(plan.count, value);
  }
  size_t Process(size_t count, float value) {
    if (!(value > 0.0f)) value = 0.0f;
    if (value > 1.0f) value = 1.0f;
    const float margin = 0.002f;
    if (!initialized_
        || (index_ + 1 < count
            && value >= static_cast<float>(index_ + 1) / count + margin)
        || (index_ > 0
            && value < static_cast<float>(index_) / count - margin)) {
      index_ = NominalIndex(count, value);
      initialized_ = true;
    }
    return index_;
  }

 private:
  bool initialized_;
  size_t index_;
};

// Plays one entry's steps. SetTone restarts the sequence but keeps phases.
class ToneVoice {
 public:
  ToneVoice() { Reset(); }
  void Reset() {
    for (size_t i = 0; i < 4; ++i) phase_[i] = 0.0f;
    entry_ = NULL;
    step_ = 0;
    position_ = 0;
    length_ = 0;
    ramp_in_ = ramp_out_ = false;
    weight_[0] = weight_[1] = 1.0f;
    max_increment_ = 0.0f;
    lfsr_ = 0xace1u;
    symbol_clock_ = 0.0f;
    symbol_offset_ = 0.0f;
    symbol_dip_ = 0.0f;
    bit_ = true;
    i_[0] = i_[1] = q_[0] = q_[1] = 0.0f;
    am_phase_ = 0.0f;
    reversal_samples_ = 0;
    reversed_ = false;
  }

  void SetTone(const ToneEntry& entry) {
    entry_ = &entry;
    max_increment_ = 0.0f;
    for (size_t s = 0; s < entry.num_steps; ++s) {
      const float top = TopFrequency(entry.steps[s]) / kSampleRate;
      if (top > max_increment_) max_increment_ = top;
    }
    EnterStep(0, true);
  }

  // MACRO: twist, the balance of a pair's low and high tones. Balanced at
  // noon; one tone alone at either end, at the single-tone level.
  void set_twist(float macro) {
    CONSTRAIN(macro, 0.0f, 1.0f);
    weight_[0] = macro > 0.5f ? 2.0f * (1.0f - macro) : 1.0f;
    weight_[1] = macro < 0.5f ? 2.0f * macro : 1.0f;
  }

  // Largest reference increment over the entry's steps, before transposition.
  float max_increment() const { return max_increment_; }

  float Next(float pitch_ratio) {
    if (entry_ == NULL) return 0.0f;
    const Step& step = entry_->steps[step_];
    float sample = Render(step, pitch_ratio);
    const size_t ramp = 48;  // 1 ms at 48 kHz, inside the step's own window.
    float envelope = 1.0f;
    if (ramp_in_ && position_ < ramp) envelope = static_cast<float>(position_) / ramp;
    if (ramp_out_ && length_ - position_ < ramp) {
      const float closing = static_cast<float>(length_ - position_ - 1) / ramp;
      if (closing < envelope) envelope = closing;
    }
    sample *= envelope;
    if (length_ == 0) {
      if (position_ < ramp) ++position_;
    } else if (++position_ >= length_) {
      EnterStep(step_ + 1 < entry_->num_steps ? step_ + 1 : 0, false);
    }
    return sample;
  }

 private:
  static float TopFrequency(const Step& step) {
    switch (step.signal) {
      case SIGNAL_TONES:
      case SIGNAL_FSK: {
        float top = 0.0f;
        for (size_t i = 0; i < 4; ++i) if (step.hz[i] > top) top = step.hz[i];
        return top;
      }
      case SIGNAL_DPSK:
      case SIGNAL_QAM:
        return step.hz[0] + 0.5f * step.rate;
      case SIGNAL_ANSAM:
        return step.hz[0] + step.rate;
      case SIGNAL_MULTITONE:
        return step.hz[1];
      default:
        return 0.0f;
    }
  }

  static bool Joins(const Step& a, const Step& b) {
    // Tones into tones stay phase-continuous; anything else ramps.
    return a.signal == b.signal && a.signal == SIGNAL_TONES;
  }

  void EnterStep(size_t index, bool restart) {
    const Step& step = entry_->steps[index];
    const Step& previous = entry_->steps[index == 0 ? entry_->num_steps - 1 : index - 1];
    const size_t next_index = index + 1 < entry_->num_steps ? index + 1 : 0;
    const Step& next = entry_->steps[next_index];
    step_ = index;
    position_ = 0;
    length_ = static_cast<size_t>(step.seconds * kSampleRate + 0.5f);
    const bool sounding = step.signal != SIGNAL_SILENCE;
    ramp_in_ = sounding && (restart || previous.signal == SIGNAL_SILENCE
        || !Joins(previous, step));
    ramp_out_ = sounding && length_ != 0 && (next.signal == SIGNAL_SILENCE
        || !Joins(step, next) || (next_index == 0 && entry_->num_steps == 1));
    symbol_clock_ = 0.0f;
    reversal_samples_ = 0;
    reversed_ = false;
  }

  float RandomUnit() {
    // Galois LFSR, x^16 + x^14 + x^13 + x^11 + 1.
    const unsigned lsb = lfsr_ & 1u;
    lfsr_ >>= 1;
    if (lsb) lfsr_ ^= 0xb400u;
    return static_cast<float>(lfsr_ & 0xffu) / 255.0f;
  }

  // True at the start of each symbol; the clock runs at the transposed rate.
  bool SymbolTick(float rate, float pitch_ratio) {
    symbol_clock_ += rate * pitch_ratio / kSampleRate;
    if (symbol_clock_ < 1.0f) return false;
    symbol_clock_ -= static_cast<int>(symbol_clock_);
    return true;
  }

  float Advance(size_t i, float hz, float pitch_ratio) {
    phase_[i] += hz * pitch_ratio / kSampleRate;
    phase_[i] -= static_cast<int>(phase_[i]);
    return phase_[i];
  }

  float Render(const Step& step, float pitch_ratio) {
    switch (step.signal) {
      case SIGNAL_TONES: {
        size_t count = 0;
        float sum = 0.0f;
        float twisted = 0.0f;
        for (size_t i = 0; i < 4; ++i) {
          if (step.hz[i] <= 0.0f) continue;
          const float sine = Sine(Advance(i, step.hz[i], pitch_ratio));
          sum += sine;
          if (count < 2) twisted += sine * weight_[count];
          ++count;
        }
        // Twist applies to pairs. One weight is always 1, so the sum is >= 1.
        if (count == 2) return 0.5f * twisted / (weight_[0] + weight_[1]);
        return count ? 0.5f * sum / count : 0.0f;
      }
      case SIGNAL_FSK: {
        if (SymbolTick(step.rate, pitch_ratio)) bit_ = RandomUnit() < 0.5f;
        return 0.5f * Sine(Advance(0, bit_ ? step.hz[0] : step.hz[1], pitch_ratio));
      }
      case SIGNAL_DPSK: {
        if (SymbolTick(step.rate, pitch_ratio)) {
          // Dibits move the carrier phase by 0, 90, 180 or 270 degrees; the
          // bigger the change, the deeper the dip a shaped symbol makes.
          const int dibit = static_cast<int>(RandomUnit() * 3.999f);
          symbol_offset_ += 0.25f * dibit;
          symbol_offset_ -= static_cast<int>(symbol_offset_);
          symbol_dip_ = dibit == 2 ? 1.0f : dibit == 0 ? 0.0f : 0.5f;
        }
        const float shape = Sine(0.5f * symbol_clock_);  // 0 at edges, 1 mid-symbol
        const float level = 1.0f - symbol_dip_ * (1.0f - shape);
        float phase = Advance(0, step.hz[0], pitch_ratio) + symbol_offset_;
        phase -= static_cast<int>(phase);
        return 0.5f * level * Sine(phase);
      }
      case SIGNAL_QAM: {
        if (SymbolTick(step.rate, pitch_ratio)) {
          i_[0] = i_[1];
          q_[0] = q_[1];
          i_[1] = RandomUnit() < 0.5f ? (RandomUnit() < 0.5f ? -1.0f : -0.33f)
              : (RandomUnit() < 0.5f ? 0.33f : 1.0f);
          q_[1] = RandomUnit() < 0.5f ? (RandomUnit() < 0.5f ? -1.0f : -0.33f)
              : (RandomUnit() < 0.5f ? 0.33f : 1.0f);
        }
        const float t = symbol_clock_;
        const float in_phase = i_[0] + (i_[1] - i_[0]) * t;
        const float quadrature = q_[0] + (q_[1] - q_[0]) * t;
        const float phase = Advance(0, step.hz[0], pitch_ratio);
        float cosine_phase = phase + 0.25f;
        cosine_phase -= static_cast<int>(cosine_phase);
        return 0.35f * (in_phase * Sine(cosine_phase) - quadrature * Sine(phase));
      }
      case SIGNAL_ANSAM: {
        // V.8 ANSam: 2100 Hz, 20% amplitude modulation at 15 Hz, and a phase
        // reversal every 450 ms.
        am_phase_ += step.rate * pitch_ratio / kSampleRate;
        am_phase_ -= static_cast<int>(am_phase_);
        const size_t interval = static_cast<size_t>(0.45f * kSampleRate / pitch_ratio);
        if (++reversal_samples_ >= interval) {
          reversal_samples_ = 0;
          reversed_ = !reversed_;
        }
        float phase = Advance(0, step.hz[0], pitch_ratio) + (reversed_ ? 0.5f : 0.0f);
        phase -= static_cast<int>(phase);
        return 0.45f * (1.0f + 0.2f * Sine(am_phase_)) * Sine(phase);
      }
      case SIGNAL_MULTITONE: {
        // V.34 line probing: tones every 150 Hz to 3750 Hz, skipping 900,
        // 1200, 1800 and 2400 Hz. Fixed per-tone phases keep the crest down.
        const float base = Advance(0, step.hz[0], pitch_ratio);
        float sum = 0.0f;
        const int top = static_cast<int>(step.hz[1] / step.hz[0] + 0.5f);
        for (int k = 1; k <= top; ++k) {
          const float hz = k * step.hz[0];
          if (hz == step.hz[2] || hz == step.hz[3]
              || hz == 2.0f * step.hz[2] || hz == 2.0f * step.hz[3]) continue;
          float phase = k * base + 0.37f * k * k;
          phase -= static_cast<int>(phase);
          sum += Sine(phase);
        }
        return 0.09f * sum;
      }
      default:
        return 0.0f;
    }
  }

  const ToneEntry* entry_;
  size_t step_;
  size_t position_;
  size_t length_;  // 0 holds the step
  bool ramp_in_;
  bool ramp_out_;
  float phase_[4];
  float weight_[2];
  float max_increment_;
  unsigned lfsr_;
  float symbol_clock_;
  float symbol_offset_;
  float symbol_dip_;
  bool bit_;
  float i_[2];
  float q_[2];
  float am_phase_;
  size_t reversal_samples_;
  bool reversed_;
};

}  // namespace phreak
}  // namespace plaits

#endif  // PLAITS_LAB_PHREAK_TONES_H_
