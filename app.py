import fitz  # PyMuPDF
import os
import tempfile
from google import genai
import time
from dotenv import load_dotenv

load_dotenv()

# ==== GLOBAL CONFIGURATIONS ====
PDF_PATH = "Science_Bengali_X.pdf"
PAGE_NUMBER = 18
OUTPUT_FOLDER = "gemini_bengali_output"
API_KEY = os.environ["GEMINI_API_KEY"]  # ===============================

def extract_specific_page(pdf_path, page_number, output_folder=None, dpi=300):
    """Convert a specific PDF page to a high-resolution image"""
    if output_folder is None:
        output_folder = tempfile.mkdtemp()
    elif not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    doc = fitz.open(pdf_path)
    if page_number <= 0 or page_number > len(doc):
        raise ValueError(f"Invalid page number. PDF has {len(doc)} pages.")
    
    page_index = page_number - 1
    page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
    
    image_path = os.path.join(output_folder, f"page_{page_number}.png")
    pix.save(image_path)
    
    return image_path

def extract_text_with_gemini(image_path, api_key):
    """Extract text from an image using Gemini API with updated format"""
    client = genai.Client(api_key=api_key)
    uploaded_file = client.files.upload(file=image_path)

    prompt = """
Understand the layout of a textbook page, which may include boxes containing text.

Your task:
1. Extract all text from the image, including text inside boxes.
2. Delimit each boxed section with  
   [START OF BOX]  
   …box contents…  
   [END OF BOX]
3. Preserve the original reading order (left→right, top→bottom).
4. In your output, include two main sections:

   **NOTES:**  
   - Text that appeared inside boxes.

   **TEXTS:**  
   - Text that appeared outside of boxes, one sentence per line.

5. Preserve all characters and formatting exactly as shown, remove unnecessary texts like page number, image marking.
6. Do not omit any visible text on the page.

Your response should clearly reflect the layout and separation.  

"""

    max_retries = 3
    backoff_time = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[uploaded_file, prompt],
            )
            return response.text
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt < max_retries - 1:
                sleep_time = backoff_time * (2 ** attempt)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                return f"Error extracting text: {str(e)}"

def process_page(pdf_path, page_number, api_key, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        print(f"Extracting page {page_number} from PDF...")
        image_path = extract_specific_page(pdf_path, page_number, output_folder)
        
        print(f"Processing page {page_number} with Gemini API...")
        page_text = extract_text_with_gemini(image_path, api_key)

        output_file = os.path.join(output_folder, f"page_{page_number}_text.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_text)
        
        print(f"Extraction complete! Results saved to {output_file}")
        return output_file
    except Exception as e:
        print(f"Error processing page {page_number}: {str(e)}")
        return None

def main():
    output_file = process_page(PDF_PATH, PAGE_NUMBER, API_KEY, OUTPUT_FOLDER)
    if output_file:
        print(f"Text extraction for page {PAGE_NUMBER} completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()
