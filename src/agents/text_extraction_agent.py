from .base_agent import BaseAgent
from google import genai
import re

class TextExtractionAgent(BaseAgent):
    """Agent responsible for text extraction from images"""
    
    def __init__(self, api_key):
        super().__init__()
        self.client = genai.Client(api_key=api_key)
    
    def extract_text(self, image_path):
        """Extract text from an image using Gemini"""
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[{"parts": [{"text": "Extract all text from this image"}, {"inline_data": {"mime_type": "image/png", "data": image_data}}]}]
            )
            return response.text
        except Exception as e:
            self.log(f"Error extracting text: {str(e)}")
            return ""
    
    def parse_sections(self, text):
        """Parse extracted text into notes and regular text"""
        notes = []
        texts = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Process each line
        current_note = []
        current_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is part of a note (box)
            if re.match(r'^[□■▢▣▤▥▦▧▨▩]', line):
                if current_text:
                    texts.append(' '.join(current_text))
                    current_text = []
                current_note.append(line)
            else:
                if current_note:
                    notes.append(' '.join(current_note))
                    current_note = []
                current_text.append(line)
        
        # Add any remaining content
        if current_note:
            notes.append(' '.join(current_note))
        if current_text:
            texts.append(' '.join(current_text))
        
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