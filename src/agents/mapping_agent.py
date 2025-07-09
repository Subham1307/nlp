import json
import re
from .base_agent import BaseAgent
from google import genai

class MappingAgent(BaseAgent):
    """Agent responsible for mapping Hindi sentences to Bengali, page-wise."""

    def __init__(self, api_key: str):
        super().__init__()
        self.client = genai.Client(api_key=api_key)

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(\S)\s(?=\S)', r'\1', text)
        return text.strip()

    def _clean_and_parse(self, raw: str) -> list[dict]:
        """
        Cleans Gemini's raw output by stripping markdown fences and parsing JSON safely.
        """
        txt = raw.strip()

        if txt.startswith("```"):
            lines = txt.splitlines()
            if lines and lines[0].startswith("```"):
                lines.pop(0)
            if lines and lines[-1].startswith("```"):
                lines.pop(-1)
            txt = "\n".join(lines)

        try:
            data = json.loads(txt)
        except Exception as e:
            self.log(f"[MappingAgent] JSON parse failed: {e}\nRaw response:\n{txt}")
            return []

        for item in data:
            item["hindi"] = self._normalize_text(item.get("hindi", ""))
            item["bengali"] = self._normalize_text(item.get("bengali", ""))

        return data

    def map_full_text(self, hindi_para: str, bengali_para: str) -> str:
        prompt = f"""
**Task Description:**
You are an expert in **Hindi** and **Bengali** languages. 
You will be given two paragraphs:

* One in **Hindi** containing multiple sentences.
* One in **Bengali** containing multiple sentences.

---

### ✅ Your Task:

1. Carefully identify **each complete Hindi sentence**, one by one.
2. For **each Hindi sentence**, find the Bengali sentence(s) that convey the **same meaning**.

   * Sometimes **one Bengali sentence** matches a Hindi sentence.
   * Sometimes **multiple Bengali sentences together** match a single Hindi sentence.
   * If **no matching Bengali translation** exists, return \"NA\".
3. **Do not assume** sentence order is identical.
4. **Avoid repeating** the same Bengali sentence for multiple mappings.
5. Be **strict**: only map sentences that **actually carry equivalent meaning**, not just similar words.
6. Return the sentences in **proper format with spacing and punctuation**.

---

### 🔢 Return Format:

Return output strictly as a JSON array:

```json
[
  {{ "hindi": "<Hindi Sentence>", "bengali": "<Bengali Translation or NA>" }}
]
```

---

### 📄 Input:

**Hindi paragraph:**
{hindi_para}

**Bengali paragraph:**
{bengali_para}

"""
        try:
            resp = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
            )
            return resp.text
        except Exception as e:
            self.log(f"[MappingAgent] Error during mapping call: {e}")
            return ""

    def execute(self, hindi_pages: list[dict], bengali_pages: list[dict]) -> list[dict]:
        """
        Perform page-wise mapping and return structured results.
        """
        results = []

        for h_pg, b_pg in zip(hindi_pages, bengali_pages):
            page_no = h_pg["page"]

            hi_para = " ".join(h_pg["texts"])
            be_para = " ".join(b_pg["texts"])

            self.log(f"[MappingAgent] Mapping page {page_no}")

            raw = self.map_full_text(hi_para, be_para)
            mappings = self._clean_and_parse(raw)

            results.append({
                "page": page_no,
                "mappings": mappings
            })

        return results
