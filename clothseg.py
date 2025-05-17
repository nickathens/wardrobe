"""U\u00b2-Net-based cloth segmentation utilities."""

import os
import json
from typing import Dict, List
import struct

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

try:
    import torch
except Exception:  # pragma: no cover - optional dependency
    torch = None

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None


class ClothClassifier:
    """Threshold-based garment category predictor."""

    DEFAULT_MODEL_PATH = os.path.join(
        os.path.expanduser("~"), ".wardrobe", "classifier.json"
    )

    def __init__(self, model_path: str | None = None):
        self.model_path = (
            model_path
            or (
                self.DEFAULT_MODEL_PATH if os.path.exists(self.DEFAULT_MODEL_PATH) else None
            )
        )
        self.classes = ["shirt", "pants", "dress"]
        self.thresholds = [1.3, 0.8]  # dress, shirt
        self.weights = None
        self.bias = None
        if self.model_path and os.path.exists(self.model_path):
            try:  # pragma: no cover - external file
                with open(self.model_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if "classes" in data:
                    self.classes = data["classes"]
                if "thresholds" in data:
                    self.thresholds = data["thresholds"]
                self.weights = data.get("weights")
                self.bias = data.get("bias")
            except Exception:
                self.weights = None
                self.bias = None
        if self.weights is None:
            self.weights = None
            self.bias = None

    def predict(self, ratio: float) -> str:
        if self.weights is not None:
            x1 = ratio
            x2 = ratio * ratio
            scores = [w[0] * x1 + w[1] * x2 + b for w, b in zip(self.weights, self.bias)]
            idx = scores.index(max(scores))
            return self.classes[idx]
        dress_thres, shirt_thres = self.thresholds
        if ratio > dress_thres:
            return "dress"
        elif ratio > shirt_thres:
            return "shirt"
        else:
            return "pants"


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

    def __init__(self, model_path: str | None = None, classifier_path: str | None = None):
        """Initialise the segmenter.

        Parameters
        ----------
        model_path : str | None
            Optional path to a pre-trained U2Net cloth segmentation model.
        classifier_path : str | None
            Optional path to a saved classifier used for garment category prediction.
        """
        if model_path is None:
            model_path = (
                self.DEFAULT_MODEL_PATH if os.path.exists(self.DEFAULT_MODEL_PATH) else None
            )
        self.model_path = model_path
        self.model = None
        self.classifier = ClothClassifier(classifier_path)
        if torch is not None and self.model_path is not None:
            try:  # pragma: no cover - external file loading
                self.model = torch.jit.load(self.model_path)
                self.model.eval()
            except Exception:
                self.model = None

    @staticmethod
    def _get_image_size(path: str) -> tuple[int, int]:
        """Return ``(width, height)`` for a PNG or JPEG image.

        This helper avoids external dependencies by reading the image header
        directly. If the size cannot be determined, ``(0, 0)`` is returned.
        """
        try:
            with open(path, "rb") as f:
                head = f.read(24)
                if len(head) >= 24 and head.startswith(b"\211PNG\r\n\032\n") and head[12:16] == b"IHDR":
                    width, height = struct.unpack(">II", head[16:24])
                    return int(width), int(height)
                if head[:2] == b"\xff\xd8":
                    f.seek(2)
                    while True:
                        byte = f.read(1)
                        if not byte:
                            break
                        if byte != b"\xff":
                            continue
                        marker = f.read(1)
                        while marker == b"\xff":
                            marker = f.read(1)
                        if marker in b"\xc0\xc1\xc2\xc3\xc5\xc6\xc7\xc9\xca\xcb\xcd\xce\xcf":
                            f.read(3)
                            height, width = struct.unpack(">HH", f.read(4))
                            return int(width), int(height)
                        else:
                            size_data = f.read(2)
                            if len(size_data) != 2:
                                break
                            size = struct.unpack(">H", size_data)[0]
                            f.seek(size - 2, 1)
        except Exception:  # pragma: no cover - fallback when parsing fails
            pass
        return 0, 0

    def _parse_grabcut(self, image_path: str) -> Dict[str, List]:
        """Return simple masks using OpenCV's GrabCut if available."""
        if cv2 is None or np is None:
            return {}
        img = cv2.imread(image_path)
        if img is None:
            return {}
        mask = np.zeros(img.shape[:2], np.uint8)
        rect = (1, 1, img.shape[1] - 2, img.shape[0] - 2)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        try:  # pragma: no cover - requires cv2
            cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        except Exception:  # pragma: no cover - grabcut failure
            return {}
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")
        if mask2.sum() == 0:
            return {}
        ys, xs = np.where(mask2 == 1)
        left, right = int(xs.min()), int(xs.max())
        top, bottom = int(ys.min()), int(ys.max())
        mid = (top + bottom) // 2
        return {
            "upper_body": [[left, top, right, mid]],
            "lower_body": [[left, mid, right, bottom]],
            "full_body": [[left, top, right, bottom]],
        }

    def classify(self, image_path: str, parts: Dict[str, List]) -> Dict[str, str]:
        """Return garment category and a basic colour estimate."""
        if cv2 is None:
            return {"category": "unknown", "color": "unknown"}
        full = parts.get("full_body")
        if not full:
            return {"category": "unknown", "color": "unknown"}
        x1, y1, x2, y2 = full[0]
        img = cv2.imread(image_path)
        if img is None:
            return {"category": "unknown", "color": "unknown"}
        region = img[y1:y2, x1:x2]
        if region.size == 0:
            return {"category": "unknown", "color": "unknown"}
        h, w = region.shape[:2]
        ratio = h / w if w else 0
        category = self.classifier.predict(ratio)
        avg_bgr = region.mean(axis=(0, 1))
        hsv = cv2.cvtColor(avg_bgr.reshape(1, 1, 3).astype("uint8"), cv2.COLOR_BGR2HSV)[0, 0]
        hval, sval, vval = hsv
        if vval > 200 and sval < 30:
            color = "white"
        elif vval < 50:
            color = "black"
        elif sval < 40:
            color = "gray"
        else:
            if hval < 15 or hval >= 165:
                color = "red"
            elif hval < 30:
                color = "orange"
            elif hval < 45:
                color = "yellow"
            elif hval < 75:
                color = "green"
            elif hval < 130:
                color = "blue"
            else:
                color = "purple"
        return {"category": category, "color": color}

    def parse(self, image_path: str) -> Dict[str, List]:
        """Return segmentation masks for the supplied image.

        If a real model is available, it will be used. Otherwise, this
        method returns dummy segmentation data so the rest of the
        application can function without the heavy dependency.
        """
        parts = ["upper_body", "lower_body", "full_body"]

        if self.model is None and torch is not None:  # pragma: no cover - load lazily
            path = self.model_path
            if path is None and os.path.exists(self.DEFAULT_MODEL_PATH):
                path = self.DEFAULT_MODEL_PATH
            if path and os.path.exists(path):
                try:
                    self.model = torch.jit.load(path)
                    self.model.eval()
                except Exception:
                    self.model = None

        if self.model is None:
            parts_gc = self._parse_grabcut(image_path)
            if parts_gc:
                return parts_gc
            width, height = self._get_image_size(image_path)
            if width == 0 or height == 0:
                return {part: [] for part in parts}
            half = height // 2
            return {
                "upper_body": [[0, 0, width, half]],
                "lower_body": [[0, half, width, height]],
                "full_body": [[0, 0, width, height]],
            }

        # Real inference path. This branch is not executed in tests as it
        # requires PyTorch and model weights.
        with torch.no_grad():  # pragma: no cover - requires torch
            image = Image.open(image_path).convert("RGB")
            tensor = torch.from_numpy(np.array(image)).float().permute(2, 0, 1) / 255.0
            tensor = tensor.unsqueeze(0)
            output = self.model(tensor)[0]
            masks = output > 0.5
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
