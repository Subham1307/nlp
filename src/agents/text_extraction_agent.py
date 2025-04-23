from .base_agent import BaseAgent
from google import genai
import re

class TextExtractionAgent(BaseAgent):
    """Agent responsible for text extraction from images"""
    
    def __init__(self, api_key):
        super().__init__()
        self.client = genai.Client(api_key=api_key)
        self.prompt = """
Understand the layout of a textbook page, which may include boxes containing text.

Your task:
1. Extract all text including text inside boxes, don't extract texts from images like image marking.
2. Delimit each boxed section with  
   [START OF BOX]  
   …box contents…  
   [END OF BOX]
3. Preserve the original reading order (left→right, top→bottom) strictly.
4. In your output, include two main sections:

   **NOTES:**  
   - Text that appeared inside boxes.

   **TEXTS:**  
   - Text that appeared outside of boxes, one sentence per line, sentences are identified until '.' occurs, keep the sentences in <> 

5. Remove unnecessary texts like page number, image marking.

Your response should clearly reflect the layout and separation.
"""
    
    def extract_text(self, image_path):
        """Extract text from an image using Gemini"""
        try:
            uploaded_file = self.client.files.upload(file=image_path)
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[uploaded_file, self.prompt],
            )
            return response.text
        except Exception as e:
            self.log(f"Error extracting text: {str(e)}")
            return ""
    
    def parse_sections(self, raw_text):
        """Split raw output into notes and texts lists"""
        notes, texts = [], []
        in_box = False
        
        for line in raw_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("[START OF BOX]"):
                in_box = True
                notes.append(stripped)
                continue
            if stripped.startswith("[END OF BOX]"):
                notes.append(stripped)
                in_box = False
                continue
            # skip section headers
            if stripped in {"**NOTES:**", "**TEXTS:**"} or not stripped:
                continue
            # collect
            if in_box:
                notes.append(stripped)
            else:
                texts.append(stripped)
                
        return notes, texts
    
    def execute(self, image_paths):
        """Extract text from images and parse into sections"""
        all_notes = []
        all_texts = []
        
        for image_path in image_paths:
            self.log(f"Extracting text from {image_path}")
            raw_text = self.extract_text(image_path)
            notes, texts = self.parse_sections(raw_text)
            all_notes.extend(notes)
            all_texts.extend(texts)
        
        return all_notes, all_texts 