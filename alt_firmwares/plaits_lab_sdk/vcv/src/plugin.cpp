// Copyright 2026 Matt Policastro.
// SPDX-License-Identifier: MIT
//
// The Rack side: Plaits' controls and jacks around LabVoice, which renders
// 12-sample blocks at 48 kHz that are resampled to Rack's rate, as VCV's own
// Plaits port does.

#include <rack.hpp>

#include <vector>

#include "lab_voice.h"

using namespace rack;
namespace lab = plaits_lab_vcv;

Plugin* pluginInstance;

struct PlaitsLabEngine : Module {
  enum ParamId {
    FREQ_PARAM,
    HARMONICS_PARAM,
    TIMBRE_PARAM,
    MORPH_PARAM,
    MACRO_PARAM,
    TIMBRE_CV_PARAM,
    FREQ_CV_PARAM,
    MORPH_CV_PARAM,
    LPG_COLOUR_PARAM,
    LPG_DECAY_PARAM,
    PARAMS_LEN
  };
  enum InputId {
    TIMBRE_INPUT,
    FREQ_INPUT,
    MORPH_INPUT,
    HARMONICS_INPUT,
    TRIGGER_INPUT,
    LEVEL_INPUT,
    NOTE_INPUT,
    INPUTS_LEN
  };
  enum OutputId { OUT_OUTPUT, AUX_OUTPUT, OUTPUTS_LEN };

  lab::LabVoice voice;
  dsp::SampleRateConverter<2> converter;
  dsp::DoubleRingBuffer<dsp::Frame<2>, 256> buffer;

  PlaitsLabEngine() {
    config(PARAMS_LEN, INPUTS_LEN, OUTPUTS_LEN);
    configParam(FREQ_PARAM, -4.f, 4.f, 0.f, "Frequency", " semitones", 0.f, 12.f);
    configParam(HARMONICS_PARAM, 0.f, 1.f, 0.5f, "Harmonics", "%", 0.f, 100.f);
    configParam(TIMBRE_PARAM, 0.f, 1.f, 0.5f, "Timbre", "%", 0.f, 100.f);
    configParam(MORPH_PARAM, 0.f, 1.f, 0.5f, "Morph", "%", 0.f, 100.f);
    configParam(MACRO_PARAM, 0.f, 1.f, 0.5f, "Macro (neutral at noon)", "%", 0.f, 100.f);
    configParam(TIMBRE_CV_PARAM, -1.f, 1.f, 0.f, "Timbre CV amount", "%", 0.f, 100.f);
    configParam(FREQ_CV_PARAM, -1.f, 1.f, 0.f, "FM amount", "%", 0.f, 100.f);
    configParam(MORPH_CV_PARAM, -1.f, 1.f, 0.f, "Morph CV amount", "%", 0.f, 100.f);
    configParam(LPG_COLOUR_PARAM, 0.f, 1.f, 0.5f, "Lowpass gate colour", "%", 0.f, 100.f);
    configParam(LPG_DECAY_PARAM, 0.f, 1.f, 0.5f, "Lowpass gate decay", "%", 0.f, 100.f);
    configInput(TIMBRE_INPUT, "Timbre");
    configInput(FREQ_INPUT, "FM");
    configInput(MORPH_INPUT, "Morph");
    configInput(HARMONICS_INPUT, "Harmonics");
    configInput(TRIGGER_INPUT, "Trigger");
    configInput(LEVEL_INPUT, "Level");
    configInput(NOTE_INPUT, "Pitch (1V/oct)");
    configOutput(OUT_OUTPUT, "Main");
    configOutput(AUX_OUTPUT, "Auxiliary");
    converter.setChannels(2);
  }

  void process(const ProcessArgs& args) override {
    if (buffer.empty()) {
      lab::Controls c;
      c.note = 60.f + params[FREQ_PARAM].getValue() * 12.f;
      c.harmonics = params[HARMONICS_PARAM].getValue();
      c.timbre = params[TIMBRE_PARAM].getValue();
      c.morph = params[MORPH_PARAM].getValue();
      c.macro = params[MACRO_PARAM].getValue();
      c.frequency_modulation_amount = params[FREQ_CV_PARAM].getValue();
      c.timbre_modulation_amount = params[TIMBRE_CV_PARAM].getValue();
      c.morph_modulation_amount = params[MORPH_CV_PARAM].getValue();
      c.lpg_colour = params[LPG_COLOUR_PARAM].getValue();
      c.decay = params[LPG_DECAY_PARAM].getValue();

      lab::Inputs in;
      in.v_oct = inputs[NOTE_INPUT].getVoltage();
      in.fm = inputs[FREQ_INPUT].getVoltage();
      in.harmonics = inputs[HARMONICS_INPUT].getVoltage();
      in.timbre = inputs[TIMBRE_INPUT].getVoltage();
      in.morph = inputs[MORPH_INPUT].getVoltage();
      in.trigger = inputs[TRIGGER_INPUT].getVoltage();
      in.level = inputs[LEVEL_INPUT].getVoltage();
      in.fm_patched = inputs[FREQ_INPUT].isConnected();
      in.timbre_patched = inputs[TIMBRE_INPUT].isConnected();
      in.morph_patched = inputs[MORPH_INPUT].isConnected();
      in.trigger_patched = inputs[TRIGGER_INPUT].isConnected();
      in.level_patched = inputs[LEVEL_INPUT].isConnected();

      float out[lab::kBlockSize], aux[lab::kBlockSize];
      voice.Render(c, in, out, aux);
      dsp::Frame<2> frames[lab::kBlockSize];
      for (size_t i = 0; i < lab::kBlockSize; i++) {
        frames[i].samples[0] = out[i];
        frames[i].samples[1] = aux[i];
      }
      converter.setRates(48000, (int) args.sampleRate);
      int in_length = lab::kBlockSize;
      int out_length = buffer.capacity();
      converter.process(frames, &in_length, buffer.endData(), &out_length);
      buffer.endIncr(out_length);
    }
    if (!buffer.empty()) {
      dsp::Frame<2> frame = buffer.shift();
      outputs[OUT_OUTPUT].setVoltage(frame.samples[0]);
      outputs[AUX_OUTPUT].setVoltage(frame.samples[1]);
    }
  }
};

// Rack's SVG renderer draws no text, so the labels are drawn here.
struct PanelLabels : TransparentWidget {
  struct Label {
    std::string text;
    float x, y, size;
    bool light;
  };
  std::vector<Label> labels;

  void draw(const DrawArgs& args) override {
    std::shared_ptr<window::Font> font = APP->window->uiFont;
    if (!font || font->handle < 0) return;
    nvgFontFaceId(args.vg, font->handle);
    nvgTextAlign(args.vg, NVG_ALIGN_CENTER | NVG_ALIGN_MIDDLE);
    for (const Label& label : labels) {
      nvgFontSize(args.vg, label.size);
      nvgFillColor(args.vg, label.light ? nvgRGB(0xf2, 0xf0, 0xea) : nvgRGB(0x2b, 0x2b, 0x2b));
      Vec p = mm2px(Vec(label.x, label.y));
      nvgText(args.vg, p.x, p.y, label.text.c_str(), NULL);
    }
  }
};

struct PlaitsLabEngineWidget : ModuleWidget {
  PlaitsLabEngineWidget(PlaitsLabEngine* module) {
    typedef PlaitsLabEngine M;
    setModule(module);
    setPanel(createPanel(asset::plugin(pluginInstance, "res/PlaitsLabEngine.svg")));

    PanelLabels* labels = new PanelLabels;
    labels->box.size = box.size;
    labels->labels = {
      {lab::LabVoice::name(), 30.48f, 8.5f, 15.f, true},
      {"PLAITS LAB", 30.48f, 14.5f, 8.f, true},
      {"FREQUENCY", 15.24f, 23.f, 8.f, false},
      {"HARMONICS", 45.72f, 23.f, 8.f, false},
      {"TIMBRE", 12.f, 43.f, 8.f, false},
      {"MACRO", 30.48f, 44.5f, 7.f, false},
      {"MORPH", 48.96f, 43.f, 8.f, false},
      {"TIMBRE", 10.16f, 58.f, 7.f, false},
      {"FM", 30.48f, 58.f, 7.f, false},
      {"MORPH", 50.8f, 58.f, 7.f, false},
      {"TIMBRE", 7.62f, 72.5f, 7.f, false},
      {"FM", 22.86f, 72.5f, 7.f, false},
      {"MORPH", 38.1f, 72.5f, 7.f, false},
      {"HARMO", 53.34f, 72.5f, 7.f, false},
      {"TRIG", 7.62f, 86.5f, 7.f, false},
      {"LEVEL", 20.32f, 86.5f, 7.f, false},
      {"V/OCT", 33.02f, 86.5f, 7.f, false},
      {"COLOUR", 45.72f, 86.5f, 6.f, false},
      {"DECAY", 55.88f, 86.5f, 6.f, false},
      {"LPG", 50.8f, 98.f, 6.f, false},
      {"OUT", 38.1f, 105.f, 7.f, false},
      {"AUX", 53.34f, 105.f, 7.f, false},
    };
    addChild(labels);

    addChild(createWidget<ScrewSilver>(Vec(RACK_GRID_WIDTH, 0)));
    addChild(createWidget<ScrewSilver>(Vec(box.size.x - 2 * RACK_GRID_WIDTH, RACK_GRID_HEIGHT - RACK_GRID_WIDTH)));

    addParam(createParamCentered<RoundLargeBlackKnob>(mm2px(Vec(15.24, 31.0)), module, M::FREQ_PARAM));
    addParam(createParamCentered<RoundLargeBlackKnob>(mm2px(Vec(45.72, 31.0)), module, M::HARMONICS_PARAM));
    addParam(createParamCentered<RoundBlackKnob>(mm2px(Vec(12.0, 50.0)), module, M::TIMBRE_PARAM));
    addParam(createParamCentered<Trimpot>(mm2px(Vec(30.48, 50.0)), module, M::MACRO_PARAM));
    addParam(createParamCentered<RoundBlackKnob>(mm2px(Vec(48.96, 50.0)), module, M::MORPH_PARAM));
    addParam(createParamCentered<Trimpot>(mm2px(Vec(10.16, 63.0)), module, M::TIMBRE_CV_PARAM));
    addParam(createParamCentered<Trimpot>(mm2px(Vec(30.48, 63.0)), module, M::FREQ_CV_PARAM));
    addParam(createParamCentered<Trimpot>(mm2px(Vec(50.8, 63.0)), module, M::MORPH_CV_PARAM));
    addParam(createParamCentered<Trimpot>(mm2px(Vec(45.72, 93.0)), module, M::LPG_COLOUR_PARAM));
    addParam(createParamCentered<Trimpot>(mm2px(Vec(55.88, 93.0)), module, M::LPG_DECAY_PARAM));

    addInput(createInputCentered<PJ301MPort>(mm2px(Vec(7.62, 79.0)), module, M::TIMBRE_INPUT));
    addInput(createInputCentered<PJ301MPort>(mm2px(Vec(22.86, 79.0)), module, M::FREQ_INPUT));
    addInput(createInputCentered<PJ301MPort>(mm2px(Vec(38.1, 79.0)), module, M::MORPH_INPUT));
    addInput(createInputCentered<PJ301MPort>(mm2px(Vec(53.34, 79.0)), module, M::HARMONICS_INPUT));
    addInput(createInputCentered<PJ301MPort>(mm2px(Vec(7.62, 93.0)), module, M::TRIGGER_INPUT));
    addInput(createInputCentered<PJ301MPort>(mm2px(Vec(20.32, 93.0)), module, M::LEVEL_INPUT));
    addInput(createInputCentered<PJ301MPort>(mm2px(Vec(33.02, 93.0)), module, M::NOTE_INPUT));

    addOutput(createOutputCentered<DarkPJ301MPort>(mm2px(Vec(38.1, 112.0)), module, M::OUT_OUTPUT));
    addOutput(createOutputCentered<DarkPJ301MPort>(mm2px(Vec(53.34, 112.0)), module, M::AUX_OUTPUT));
  }
};

Model* modelPlaitsLabEngine = createModel<PlaitsLabEngine, PlaitsLabEngineWidget>("PlaitsLabEngine");

void init(Plugin* p) {
  pluginInstance = p;
  p->addModel(modelPlaitsLabEngine);
}
