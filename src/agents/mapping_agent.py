import json
from .base_agent import BaseAgent
from google import genai

class MappingAgent(BaseAgent):
    """Agent responsible for mapping Hindi sentences to Bengali, page-wise."""

    def __init__(self, api_key: str):
        super().__init__()
        self.client = genai.Client(api_key=api_key)

    def map_full_text(self, hindi_para: str, bengali_para: str) -> str:
        """
        Ask Gemini to map each Hindi sentence in hindi_para to its Bengali translation(s)
        in bengali_para, combining multiple Bengali sentences if needed, and returning NA
        when no match is found.
        """
        prompt = f"""
You will be given two paragraphs: one containing Hindi sentences and the other containing Bengali sentences.
Think step by step : 
First understand the Hindi sentence, from where a sentence starts and where it ends. This is our target sentence.
Now from the bengali paragraph, find which part is the translation of out target hindi sentence, combine all them in a single string.
Go to next Hindi sentence, and keep doing this 
Dont give same sentence twice
If no translation exists, return "NA".

Return only a JSON array of objects with keys:
- "hindi": the Hindi sentence
- "bengali": the combined Bengali sentence(s) or "NA"

Hindi paragraph:
{hindi_para}

Bengali paragraph:
{bengali_para}
"""
        try:
            resp = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt],
            )
            return resp.text
        except Exception as e:
            self.log(f"[MappingAgent] Error during mapping call: {e}")
            return ""

    def _clean_and_parse(self, raw: str) -> list[dict]:
        """
        Strip markdown code fences if present, then parse JSON.
        """
        txt = raw.strip()
        if txt.startswith("```"):
            lines = txt.splitlines()
            if lines and lines[0].startswith("```"):
                lines.pop(0)
            if lines and lines[-1].startswith("```"):
                lines.pop(-1)
            txt = "\n".join(lines)
        return json.loads(txt)

    def execute(self, hindi_pages: list[dict], bengali_pages: list[dict]) -> list[dict]:
        """
        Perform page-wise mapping. Inputs:
          hindi_pages: [
            { "page": 1, "texts": [...], "notes": [...] },
            { "page": 2, ... }, ...
          ]
          bengali_pages: same shape for Bengali.

        Returns:
          [
            {
              "page": 1,
              "mappings": [
                  { "hindi": "...", "bengali": "..." }, …
              ]
            },
            ...
          ]
        """
        results = []

        for h_pg, b_pg in zip(hindi_pages, bengali_pages):
            page_no = h_pg["page"]
            # combine only the TEXTS for mapping; include 'notes' if desired
            hi_para = " ".join(h_pg["texts"])
            be_para = " ".join(b_pg["texts"])

            self.log(f"[MappingAgent] Mapping page {page_no}")
            raw = self.map_full_text(hi_para, be_para)

            try:
                mappings = self._clean_and_parse(raw)
            except Exception as e:
                self.log(f"[MappingAgent] JSON parse error on page {page_no}: {e}")
                mappings = []

            # Ensure every Hindi sentence gets a mapping (NA if missing)
            seen_hi = {m["hindi"] for m in mappings}
            for sentence in h_pg["texts"]:
                if sentence not in seen_hi:
                    mappings.append({ "hindi": sentence, "bengali": "NA" })

            results.append({
                "page": page_no,
                "mappings": mappings
            })

        return results
