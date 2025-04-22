import fitz  # PyMuPDF
import os
import tempfile
from google import genai
import time
from dotenv import load_dotenv

load_dotenv()

# ==== GLOBAL CONFIGURATIONS ====
PDF_PATH = "Science_Hindi_X.pdf"
PAGE_START = 1    # inclusive start page number
PAGE_END = 18       # inclusive end page number
OUTPUT_FOLDER = "gemini_hindi_output"
API_KEY = os.environ.get("GEMINI_API_KEY")  # ensure this is set in your environment


def extract_specific_page(pdf_path, page_number, output_folder=None, dpi=300):
    """Convert a specific PDF page to a high-resolution image"""
    if output_folder is None:
        output_folder = tempfile.mkdtemp()
    elif not os.path.exists(output_folder):
        os.makedirs(output_folder)

    doc = fitz.open(pdf_path)
    if page_number < 1 or page_number > len(doc):
        raise ValueError(f"Invalid page number. PDF has {len(doc)} pages.")

    page = doc[page_number - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
    image_path = os.path.join(output_folder, f"page_{page_number}.png")
    pix.save(image_path)
    return image_path


def extract_text_with_gemini(image_path, api_key):
    """Extract text from an image using Gemini API"""
    client = genai.Client(api_key=api_key)
    uploaded_file = client.files.upload(file=image_path)

    prompt = """
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
   - Text that appeared outside of boxes, one sentence per line, , sentences are identified until '|' occurs,  keep the sentences in <> 

5. Remove unnecessary texts like page number, image marking.


Your response should clearly reflect the layout and separation.

"""

    # retry logic
    max_retries, backoff = 3, 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[uploaded_file, prompt],
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(backoff * (2 ** attempt))
            else:
                raise


def parse_sections(raw_text):
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


def process_pages(pdf_path, start_page, end_page, api_key, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    all_notes, all_texts = [], []

    for page_number in range(start_page, end_page + 1):
        print(f"Processing page {page_number}...")
        image_path = extract_specific_page(pdf_path, page_number, output_folder)
        raw = extract_text_with_gemini(image_path, api_key)
        notes, texts = parse_sections(raw)
        all_notes.extend(notes)
        all_texts.extend(texts)

    # write merged output
    merged_file = os.path.join(output_folder, "all_pages_merged.txt")
    with open(merged_file, 'w', encoding='utf-8') as f:
        f.write("**NOTES:**\n")
        f.write("\n".join(all_notes))
        f.write("\n\n**TEXTS:**\n")
        f.write("\n".join(all_texts))

    print(f"Merged output saved to {merged_file}")


def main():
    process_pages(PDF_PATH, PAGE_START, PAGE_END, API_KEY, OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
