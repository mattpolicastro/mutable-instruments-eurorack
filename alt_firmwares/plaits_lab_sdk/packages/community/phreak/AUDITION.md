# Phreak listening notes

Listening is the human check before submission. Render any declared preview to
a WAV, or play the package live (`plaits_lab.py dev`, or the VCV test bench):

```sh
python3 alt_firmwares/plaits_lab_sdk/plaits_lab.py render \
  alt_firmwares/plaits_lab_sdk/packages/community/phreak \
  --scenario <preview-id> --output /tmp/<preview-id>.wav
```

MAIN and AUX are rendered as left and right. At LINE's noon they are identical.

## Checklist

Tick each item, and note anything that sounds wrong, harsh or unconvincing.

### Recognisable signals

- [ ] `na-dial`, `na-key-5`, `na-busy`, `na-ringback`: they sound like a North
      American phone line.
- [ ] `na-sweep`: every keypad tone is distinct; selection changes are smooth.
- [ ] `uk-ring`, `uk-engaged`, `uk-congestion`: the UK double ring is unmistakable.
- [ ] `europe-ring`, `europe-busy`, `japan-ring`: the single 425 Hz tones and
      Japan's warbled ringback read as those countries.
- [ ] `blue-box-seize`, `blue-box-call`: 2600 Hz and the MF digits sound like
      the blue box.
- [ ] `red-box-quarter`, `sit-intercept`, `off-hook-howler`: coin beeps, the
      "doo-dee-doo" intercept, and the howler are recognisable.
- [ ] `modem-answer` through `modem-connect`: the connect sequence sounds like
      dial-up, from dial tone to the training hiss.

### Controls

- [ ] `line-analog`, `line-digital`, `line-sweep`: both sides of LINE are
      useful; noon is clean; neither extreme is unpleasantly loud.
- [ ] `twist-sweep`: TWIST moves smoothly from the low tone to the high tone.
- [ ] `na-keypress`: patched keypresses are short, clean and click-free.
- [ ] `system-sweep`: moving between systems is smooth.
- [ ] `pitch-low`, `pitch-high`: transposition is musical.

### Hardware (after the `--cpu-probe` build)

- [ ] Every system plays without glitches on the module, including the V.34
      probe (`modem`, MORPH about 0.79) and `connect`.
- [ ] Patched keypresses respond immediately to a sequencer.
- [ ] Output levels sit comfortably beside stock models.

## Observations

_Record what you hear, with the date and the preview or control settings._
