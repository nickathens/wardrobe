"""Stub for cloth segmentation using a U2Net-based model."""

from typing import Dict, List

try:
    import torch
    from PIL import Image
    import numpy as np
except ImportError:  # pragma: no cover - optional dependencies
    torch = None


class ClothSegmenter:
    """Placeholder for a U2Net-based cloth segmentation model."""

    def __init__(self, model_path: str | None = None):
        """Initialise the segmenter.

        Parameters
        ----------
        model_path : str | None
            Optional path to a pre-trained U2Net cloth segmentation model.
        """
        self.model_path = model_path
        self.model = None
        if torch is not None and model_path is not None:
            try:  # pragma: no cover - external file loading
                self.model = torch.jit.load(model_path)
                self.model.eval()
            except Exception:
                self.model = None

    def parse(self, image_path: str) -> Dict[str, List]:
        """Return segmentation masks for the supplied image.

        If a real model is available, it will be used. Otherwise, this
        method returns dummy segmentation data so the rest of the
        application can function without the heavy dependency.
        """
        if self.model is None:  # pragma: no cover - dummy path
            parts = [
                "upper_body",
                "lower_body",
                "full_body",
            ]
            return {part: [] for part in parts}

        # Real inference path. This branch is not executed in tests as it
        # requires PyTorch and model weights.
        with torch.no_grad():  # pragma: no cover - requires torch
            image = Image.open(image_path).convert("RGB")
            tensor = torch.from_numpy(np.array(image)).float().permute(2, 0, 1) / 255.0
            tensor = tensor.unsqueeze(0)
            output = self.model(tensor)[0]
            masks = output > 0.5
            parts = ["upper_body", "lower_body", "full_body"]
            return {p: m.squeeze().cpu().numpy().tolist() for p, m in zip(parts, masks)}
