import re
from .base_agent import BaseAgent
from google import genai

class TextExtractionAgent(BaseAgent):
    """Agent responsible for text extraction from images, with page tagging."""

    def __init__(self, api_key):
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.prompt = """
Understand the layout of a textbook page, which may include boxes containing text.

Your task:
1. Extract all text including text inside boxes; don't extract text from images or figure labels.
2. Delimit each boxed section with  
   [START OF BOX]  
   …box contents…  
   [END OF BOX]
3. Preserve the original reading order (left→right, top→bottom) strictly.
4. In your output, include two main sections:

   **NOTES:**  
   - Text that appeared inside boxes.

   **TEXTS:**  
   - Text that appeared outside of boxes.

5. Remove unnecessary text like page numbers, figure labels, or watermarks.

Your response should clearly reflect the layout and separation.
"""

    def extract_text(self, image_path: str) -> str:
        """Upload a page image and run Gemini to extract its raw annotated text."""
        try:
            uploaded_file = self.client.files.upload(file=image_path)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[uploaded_file, self.prompt],
            )
            return response.text
        except Exception as e:
            self.log(f"[TextExtractionAgent] Error extracting text from {image_path}: {e}")
            return ""

    def parse_sections(self, raw_text: str) -> tuple[list[str], list[str]]:
        """
        Parse Gemini’s annotated text into two lists:
        - notes: all lines that were inside [START OF BOX]…[END OF BOX]
        - texts: all other lines
        """
        notes: list[str] = []
        texts: list[str] = []
        in_box = False

        for line in raw_text.splitlines():
            stripped = line.strip()
            # detect start/end of boxed sections
            if stripped.startswith("[START OF BOX]"):
                in_box = True
                notes.append(stripped)
                continue
            if stripped.startswith("[END OF BOX]"):
                notes.append(stripped)
                in_box = False
                continue
            # skip the section headers and empty lines
            if stripped in {"**NOTES:**", "**TEXTS:**"} or not stripped:
                continue
            # append to the appropriate list
            if in_box:
                notes.append(stripped)
            else:
                texts.append(stripped)

        return notes, texts

    def execute(self, image_paths: list[str]) -> list[dict]:
        """
        Process a list of page-image paths and return a list of dicts:
        [
          {
            "page": 1,
            "notes":   [...],   # boxed text lines for page 1
            "texts":   [...]    # normal text lines for page 1
          },
          {
            "page": 2,
            "notes":   [...],
            "texts":   [...]
          },
          ...
        ]
        """
        pages: list[dict] = []

        for idx, image_path in enumerate(image_paths, start=1):
            self.log(f"[TextExtractionAgent] Extracting text from page {idx}: {image_path}")
            raw = self.extract_text(image_path)
            notes, texts = self.parse_sections(raw)
            pages.append({
                "page": idx,
                "notes": notes,
                "texts": texts
            })

        return pages
