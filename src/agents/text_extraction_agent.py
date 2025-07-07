import re
from .base_agent import BaseAgent
from google import genai

class TextExtractionAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.prompt = """
Understand the layout of a textbook page, which may include boxes containing text.

Your task:
 Extract all sentence line by line, including text inside boxes; don't extract text from images or figure labels.
 It should be a proper sentence, not just a word or phrase.
 Preserve the original reading order (left→right, top→bottom) strictly.
 Remove unnecessary text like page numbers, figure labels, or watermarks.
 Don't preempt, just extract the sentences from the image.

Your response should clearly reflect the layout and separation.
"""

    def extract_text(self, image_path: str) -> str:
        """Upload a page image and run Gemini to extract its raw annotated text."""
        try:
            uploaded_file = self.client.files.upload(file=image_path)
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[uploaded_file, self.prompt],
            )
            return response.text
        except Exception as e:
            self.log(f"[TextExtractionAgent] Error extracting text from {image_path}: {e}")
            return ""


    def execute(self, image_paths: list[str]) -> list[dict]:
        """
        Process a list of page-image paths and return a list of dicts:
        [
          {
            "page": 1,
            "texts":   [...]  # raw text extracted from the page
          },
          {
            "page": 2,
            "texts":   [...]
          },
          ...
        ]
        """
        pages: list[dict] = []

        for idx, image_path in enumerate(image_paths, start=1):
            self.log(f"[TextExtractionAgent] Extracting text from page {idx}: {image_path}")
            raw = self.extract_text(image_path)
            print("raw text from page ",idx,"is ",raw)  # Debugging output
            pages.append({
                "page": idx,
                "texts": raw
            })

        return pages
