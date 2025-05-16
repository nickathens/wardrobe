"""U\u00b2-Net-based cloth segmentation utilities."""

import os
from typing import Dict, List

try:
    import torch
    from PIL import Image
    import numpy as np
except ImportError:  # pragma: no cover - optional dependencies
    torch = None


class ClothSegmenter:
    """U\u00b2-Net cloth segmentation model loader and parser."""

    #: URL for the official pre-trained weights
    MODEL_URL = (
        "https://github.com/xuebinqin/U-2-Net/releases/download/v1.0/u2net.pth"
    )

    #: Default location for the downloaded weights
    DEFAULT_MODEL_PATH = os.path.join(
        os.path.expanduser("~"), "\.u2net", "u2net.pth"
    )

    @classmethod
    def download_model(cls, dest_path: str | None = None) -> str:
        """Download the pre-trained weights.

        Parameters
        ----------
        dest_path : str | None, optional
            Location where the model should be stored. When ``None`` the
            :data:`DEFAULT_MODEL_PATH` is used.

        Returns
        -------
        str
            The path to the downloaded weights.
        """

        if torch is None:
            raise RuntimeError("PyTorch is required to download the model")

        dest = dest_path or cls.DEFAULT_MODEL_PATH
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        torch.hub.download_url_to_file(cls.MODEL_URL, dest, progress=True)
        return dest

    def __init__(self, model_path: str | None = None):
        """Initialise the segmenter.

        Parameters
        ----------
        model_path : str | None
            Optional path to a pre-trained U2Net cloth segmentation model.
        """
        if model_path is None:
            model_path = (
                self.DEFAULT_MODEL_PATH if os.path.exists(self.DEFAULT_MODEL_PATH) else None
            )
        self.model_path = model_path
        self.model = None
        if torch is not None and self.model_path is not None:
            try:  # pragma: no cover - external file loading
                self.model = torch.jit.load(self.model_path)
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


if __name__ == "__main__":  # pragma: no cover - manual invocation
    import argparse

    parser = argparse.ArgumentParser(description="U\u00b2-Net cloth segmentation utilities")
    parser.add_argument(
        "--download-model",
        action="store_true",
        help="Download the pre-trained U\u00b2-Net weights",
    )
    parser.add_argument(
        "--dest", type=str, default=None, help="Custom path for downloaded weights"
    )
    args = parser.parse_args()

    if args.download_model:
        path = ClothSegmenter.download_model(args.dest)
        print(f"Model downloaded to {path}")
