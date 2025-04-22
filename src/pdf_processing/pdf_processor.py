import fitz  # PyMuPDF
import os
import tempfile

class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def extract_specific_page(self, page_number, output_folder=None, dpi=300):
        """Convert a specific PDF page to a high-resolution image"""
        if output_folder is None:
            output_folder = tempfile.mkdtemp()
        elif not os.path.exists(output_folder):
            os.makedirs(output_folder)

        if page_number < 1 or page_number > len(self.doc):
            raise ValueError(f"Invalid page number. PDF has {len(self.doc)} pages.")

        page = self.doc[page_number - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
        image_path = os.path.join(output_folder, f"page_{page_number}.png")
        pix.save(image_path)
        return image_path

    def close(self):
        """Close the PDF document"""
        self.doc.close() 