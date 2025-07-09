import re
from .base_agent import BaseAgent
from google import genai

class BengaliTextExtractionAgent(BaseAgent):
    def __init__(self, api_key):
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.prompt = """
**Task Description**
Understand the layout of a textbook page written in **Bengali**, which may include **boxes containing sentences**.

---

### ✅ Your Task:

* Extract **all Bengali sentences**, **line by line**, exactly as they appear.
* **Do not** extract text from **images** or **figure labels**.
* Extract only **complete sentences**, **not just words or phrases**.
* Preserve the **original reading order**:
  → **Left to Right**, then **Top to Bottom**
* **Remove** irrelevant items like:

  * Page numbers
  * Watermarks
  * Figure or diagram labels

---

### ⚠️ Do Not:

* Interpret, summarize, or rephrase any content.
* Add or assume anything that is not present in the image.
* Extract partial or out-of-context words except at the end of the page there might be some words.
* Return anything other than hindi sentences like "here are the hindi senteces" or "here are the senteces in box" or "texts from box"

---

### 🎯 Final Output:

Your response should **clearly reflect the layout and sentence separation**, maintaining a structured and clean extraction.
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

    def _to_sentence_list(self, raw_text: str) -> list[str]:
        """
        Convert raw extracted text into a clean list of sentences.
        Handles bullets, numbering, and common Bengali punctuation.
        """
        lines = raw_text.splitlines()
        sentences = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove leading bullets or numbering
            line = re.sub(r"^[-*\d.\)\s]+", "", line)
            if line:
                sentences.append(line)

        return sentences

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
            sentence_list = self._to_sentence_list(raw)
            pages.append({
                "page": idx,
                "texts": sentence_list
            })

        return pages
