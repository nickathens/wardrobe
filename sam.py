class SAMSegmenter:
    """Placeholder for Segment Anything Model integration."""

    def __init__(self):
        # In a real implementation, this would load the SAM model weights.
        self.model = None

    def segment(self, image_path: str, prompt: str | None = None):
        """Return fake SAM segmentation results for the given image.

        Parameters
        ----------
        image_path : str
            Path to the image to process.
        prompt : str | None, optional
            Optional text prompt describing the object to segment.

        Returns
        -------
        dict
            A dictionary containing dummy bounding boxes and masks.
        """
        # This is only a stub and does not perform real segmentation.
        segments = [
            {
                "label": "shirt",
                "bbox": [10, 10, 50, 50],
                "mask": [],
            },
            {
                "label": "pants",
                "bbox": [20, 60, 60, 120],
                "mask": [],
            },
        ]
        return {"segments": segments}
