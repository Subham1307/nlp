import json
from .base_agent import BaseAgent
from google import genai

class MappingAgent(BaseAgent):
    """Agent responsible for mapping sentences between languages"""
    
    def __init__(self, api_key):
        super().__init__()
        self.client = genai.Client(api_key=api_key)
    
    def map_batch(self, hindi_batch, bengali_batch):
        """Map a batch of Hindi and Bengali sentences"""
        prompt = f"""Given these Hindi and Bengali sentences, map which Hindi sentence corresponds to which Bengali sentence.
        Return the mapping as a JSON array of objects with 'hindi' and 'bengali' keys.
        
        Hindi sentences:
        {hindi_batch}
        
        Bengali sentences:
        {bengali_batch}
        
        Return only the JSON array, nothing else."""
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt],
            )
            return response.text
        except Exception as e:
            self.log(f"Error in mapping batch: {str(e)}")
            return []
    
    def execute(self, hindi_texts, bengali_texts, batch_size=10, overlap=2):
        """Map Hindi sentences to their Bengali translations using overlapping batches"""
        mappings = []
        seen_pairs = set()  # To track already mapped pairs
        
        # Process texts in overlapping batches
        for i in range(0, len(hindi_texts), batch_size - overlap):
            hindi_batch = hindi_texts[i:i + batch_size]
            bengali_batch = bengali_texts[i:i + batch_size]
            
            self.log(f"Processing batch {i//(batch_size-overlap) + 1}")
            
            # Get mappings for this batch
            raw_mappings = self.map_batch(hindi_batch, bengali_batch)
            
            # Process raw mappings
            raw = raw_mappings.strip()
            if raw.startswith("```"):
                lines = raw.splitlines()
                if lines[0].startswith("```"):
                    lines.pop(0)
                if lines and lines[-1].startswith("```"):
                    lines.pop(-1)
                raw = "\n".join(lines)
            
            try:
                batch_mappings = json.loads(raw)
                
                # Add only new mappings
                for mapping in batch_mappings:
                    pair_key = (mapping['hindi'], mapping['bengali'])
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        mappings.append(mapping)
            except json.JSONDecodeError as e:
                self.log(f"Error parsing JSON from batch: {str(e)}")
                continue
        
        return mappings 