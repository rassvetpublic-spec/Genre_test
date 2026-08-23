# ARCHITECTURE

## v0.2 data flow

```text
Windows GUI / CLI
      |
      v
file or recursive folder input
      |
      v
audio decode -> representative windows -> MAEST Discogs 519
      |                                  |
      |                                  v
      |                         raw style probabilities
      v                                  |
BPM / key / spectral features            v
      |                          broad family aggregation
      |                                  |
      +-------------------------+--------+
                                v
                         genre resolver
                     primary/hybrid/confidence
                                |
                                v
                      JSON / summary CSV / GUI
```

## Design rules

- preserve raw classifier outputs separately from resolved human labels
- do not claim a single definitive genre when top broad families are nearly tied
- GUI is a presentation/input layer; analysis logic remains shared with CLI
- long ML work runs outside the Tk main thread
- no model weights are stored in Git
- raw audio/video and generated `results/` are ignored by Git
