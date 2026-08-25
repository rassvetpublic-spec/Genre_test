from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from .cancellation import CancelCheck, check_cancel
from .hf_runtime import configure_hf_runtime
from .model_config import (
    DEFAULT_SEMANTIC_MODEL,
    DEFAULT_SEMANTIC_MODEL_REVISION,
    DEFAULT_SEMANTIC_TOP_K,
)
from .models import SemanticEvidence, StyleScore
from .performance import append_perf, clock, elapsed_seconds, milliseconds

VOCAL_LABELS = {
    "singing",
    "choir",
    "chant",
    "mantra",
    "male singing",
    "female singing",
    "child singing",
    "synthetic singing",
    "rapping",
    "humming",
    "vocal music",
    "a capella",
}

MOOD_LABELS = {
    "happy music",
    "funny music",
    "sad music",
    "tender music",
    "exciting music",
    "angry music",
    "scary music",
}

GENRE_LABELS = {
    "pop music",
    "hip hop music",
    "rock music",
    "heavy metal",
    "punk rock",
    "grunge",
    "progressive rock",
    "rock and roll",
    "psychedelic rock",
    "rhythm and blues",
    "soul music",
    "reggae",
    "country",
    "swing music",
    "bluegrass",
    "funk",
    "folk music",
    "middle eastern music",
    "jazz",
    "disco",
    "classical music",
    "opera",
    "electronic music",
    "house music",
    "techno",
    "dubstep",
    "drum and bass",
    "electronica",
    "electronic dance music",
    "ambient music",
    "trance music",
    "music of latin america",
    "salsa music",
    "flamenco",
    "blues",
    "new-age music",
    "vocal music",
}

INSTRUMENT_LABELS = {
    "musical instrument",
    "guitar",
    "electric guitar",
    "bass guitar",
    "acoustic guitar",
    "steel guitar, slide guitar",
    "piano",
    "electric piano",
    "keyboard (musical)",
    "organ",
    "electronic organ",
    "hammond organ",
    "synthesizer",
    "drum kit",
    "drum",
    "snare drum",
    "bass drum",
    "timpani",
    "tabla",
    "cymbal",
    "hi-hat",
    "wood block",
    "tambourine",
    "maraca",
    "gong",
    "tubular bells",
    "mallet percussion",
    "marimba, xylophone",
    "glockenspiel",
    "vibraphone",
    "steelpan",
    "orchestra",
    "brass instrument",
    "french horn",
    "trumpet",
    "trombone",
    "bowed string instrument",
    "string section",
    "violin, fiddle",
    "cello",
    "double bass",
    "wind instrument, woodwind instrument",
    "flute",
    "saxophone",
    "clarinet",
    "harp",
    "bell",
    "accordion",
    "harmonica",
    "banjo",
    "mandolin",
    "ukulele",
}

PRODUCTION_LABELS = {
    "electronic music",
    "electronica",
    "electronic dance music",
    "synthesizer",
    "drum machine",
    "sampler",
    "distortion",
    "effects unit",
}


def _normalized(label: str) -> str:
    return label.strip().casefold()


def _filter_group(
    tags: Iterable[StyleScore],
    labels: set[str],
    *,
    limit: int,
    min_score: float = 0.03,
) -> list[StyleScore]:
    matches = [item for item in tags if _normalized(item.label) in labels and item.score >= min_score]
    return matches[:limit]


def group_semantic_tags(tags: list[StyleScore]) -> dict[str, list[StyleScore]]:
    """Split AudioSet output into the music-specific evidence used by AudioProfile."""
    return {
        "genre": _filter_group(tags, GENRE_LABELS, limit=8),
        "mood": _filter_group(tags, MOOD_LABELS, limit=5),
        "vocal": _filter_group(tags, VOCAL_LABELS, limit=5),
        "instrument": _filter_group(tags, INSTRUMENT_LABELS, limit=8),
        "production": _filter_group(tags, PRODUCTION_LABELS, limit=5),
    }


class SemanticTagger:
    """Independent AudioSet AST tagger used alongside MAEST.

    The model is intentionally loaded lazily by GenreAnalyzer. It shares the
    repo-local Hugging Face model cache, but keeps the user's normal HF auth home.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_SEMANTIC_MODEL,
        revision: str | None = DEFAULT_SEMANTIC_MODEL_REVISION,
        device: str = "auto",
    ) -> None:
        configure_hf_runtime()
        import torch
        from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

        normalized_device = device.lower().strip()
        if normalized_device not in {"auto", "cpu", "cuda"}:
            raise ValueError("semantic device must be auto, cpu or cuda")
        if normalized_device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested for semantic model but CUDA is unavailable")

        self.model_id = model_id
        self.revision = revision
        self.resolved_device = (
            "cuda" if normalized_device == "auto" and torch.cuda.is_available() else normalized_device
        )
        if self.resolved_device == "auto":
            self.resolved_device = "cpu"

        started = clock()
        self.extractor = AutoFeatureExtractor.from_pretrained(model_id, revision=revision)
        self.model = AutoModelForAudioClassification.from_pretrained(
            model_id,
            revision=revision,
            use_safetensors=True,
        )
        self.model.to(self.resolved_device)
        self.model.eval()
        self._torch = torch
        append_perf(
            "semantic_init",
            model_id=model_id,
            model_revision=revision,
            device=self.resolved_device,
            elapsed_ms=milliseconds(elapsed_seconds(started)),
        )

    def predict(
        self,
        windows: list[np.ndarray],
        sample_rate: int,
        *,
        top_k: int = DEFAULT_SEMANTIC_TOP_K,
        cancel_check: CancelCheck | None = None,
    ) -> SemanticEvidence:
        if not windows:
            return SemanticEvidence(
                model_id=self.model_id,
                model_revision=self.revision,
                device=self.resolved_device,
                windows_analyzed=0,
                top_tags=[],
                genre_tags=[],
                mood_tags=[],
                vocal_tags=[],
                instrument_tags=[],
                production_tags=[],
                status="skipped",
                notes=("no semantic windows",),
            )

        check_cancel(cancel_check)
        started = clock()
        inputs = self.extractor(
            windows,
            sampling_rate=sample_rate,
            return_tensors="pt",
        )
        inputs = {name: value.to(self.resolved_device) for name, value in inputs.items()}
        with self._torch.inference_mode():
            logits = self.model(**inputs).logits
            probabilities = self._torch.sigmoid(logits).mean(dim=0).detach().cpu().numpy()
        check_cancel(cancel_check)

        count = min(max(1, top_k), int(probabilities.shape[0]))
        indices = np.argsort(probabilities)[::-1][:count]
        id2label = self.model.config.id2label
        tags = [
            StyleScore(
                str(id2label.get(int(index), id2label.get(str(int(index)), str(int(index))))),
                round(float(probabilities[int(index)]), 6),
            )
            for index in indices
        ]
        groups = group_semantic_tags(tags)
        duration = elapsed_seconds(started)
        append_perf(
            "semantic_batch",
            model_id=self.model_id,
            model_revision=self.revision,
            device=self.resolved_device,
            windows=len(windows),
            elapsed_ms=milliseconds(duration),
            avg_window_ms=milliseconds(duration / len(windows)),
        )
        return SemanticEvidence(
            model_id=self.model_id,
            model_revision=self.revision,
            device=self.resolved_device,
            windows_analyzed=len(windows),
            top_tags=tags,
            genre_tags=groups["genre"],
            mood_tags=groups["mood"],
            vocal_tags=groups["vocal"],
            instrument_tags=groups["instrument"],
            production_tags=groups["production"],
            status="ok",
        )
