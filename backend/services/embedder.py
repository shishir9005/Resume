import numpy as np
from fastembed import TextEmbedding


class Embedder:
    """Stands in for SentenceTransformer: same MiniLM model, ONNX runtime, no PyTorch."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if "/" not in model_name:
            model_name = f"sentence-transformers/{model_name}"
        self._model = TextEmbedding(model_name=model_name)

    def encode(self, text: str, convert_to_tensor: bool = False) -> np.ndarray:
        return np.asarray(next(iter(self._model.embed([text]))), dtype=np.float32)

    def encode_many(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts in one batch. Returns shape (len(texts), dim)."""
        return np.asarray(list(self._model.embed(texts)), dtype=np.float32)
