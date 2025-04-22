import os
from dotenv import load_dotenv
from pdf_processing.pdf_processor import PDFProcessor
from text_extraction.gemini_extractor import GeminiExtractor, TextParser
from utils.file_handler import FileHandler

# Load environment variables
load_dotenv()

# Global configurations
PDF_PATH = "Science_Bengali_X.pdf"
PAGE_START = 17     # inclusive start page number
PAGE_END = 32       # inclusive end page number
OUTPUT_FOLDER = "gemini_bengali_output"
API_KEY = os.environ.get("GEMINI_API_KEY")

def process_pages(pdf_path, start_page, end_page, api_key, output_folder):
    """Process multiple pages of a PDF and extract text"""
    # Initialize components
    pdf_processor = PDFProcessor(pdf_path)
    gemini_extractor = GeminiExtractor(api_key)
    file_handler = FileHandler()
    
    # Ensure output directory exists
    file_handler.ensure_directory_exists(output_folder)
    
    all_notes, all_texts = [], []
    
    try:
        for page_number in range(start_page, end_page + 1):
            print(f"Processing page {page_number}...")
            
            # Extract page as image
            image_path = pdf_processor.extract_specific_page(page_number, output_folder)
            
            # Extract text using Gemini
            raw_text = gemini_extractor.extract_text(image_path)
            
            # Parse the extracted text
            notes, texts = TextParser.parse_sections(raw_text)
            all_notes.extend(notes)
            all_texts.extend(texts)
        
        # Write merged output
        merged_file = file_handler.write_merged_output(output_folder, all_notes, all_texts)
        print(f"Merged output saved to {merged_file}")
        
    finally:
        pdf_processor.close()

def main():
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    process_pages(PDF_PATH, PAGE_START, PAGE_END, API_KEY, OUTPUT_FOLDER)

if __name__ == "__main__":
    main() 