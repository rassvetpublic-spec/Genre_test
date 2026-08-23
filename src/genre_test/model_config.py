DEFAULT_MODEL = "mtg-upf/discogs-maest-30s-pw-129e-519l"
DEFAULT_MODEL_REVISION = "6c35f32a350f74351870937d5ae0bae1d898d1df"
DEFAULT_CUDA_BATCH_SIZE = 8

# Independent semantic/audio-event classifier used by the v0.4 AudioProfile layer.
# AudioSet gives broad music genres plus vocals, instruments and mood/event tags.
DEFAULT_SEMANTIC_MODEL = "MIT/ast-finetuned-audioset-10-10-0.4593"
DEFAULT_SEMANTIC_MODEL_REVISION = "f826b80d28226b62986cc218e5cec390b1096902"
DEFAULT_SEMANTIC_WINDOW_SECONDS = 10.0
DEFAULT_SEMANTIC_WINDOW_COUNT = 3
DEFAULT_SEMANTIC_TOP_K = 40
