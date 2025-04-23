import os
import tempfile
from .base_agent import BaseAgent
import fitz  # PyMuPDF

class PDFAgent(BaseAgent):
    """Agent responsible for PDF processing operations"""
    
    def __init__(self):
        super().__init__()
        self.temp_dir = None
    
    def extract_specific_page(self, pdf_path, page_number, output_folder):
        """Extract a specific page from PDF as an image"""
        try:
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # Get the page
            page = doc[page_number - 1]  # 0-based index
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            # Create output directory if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)
            
            # Save the image
            image_path = os.path.join(output_folder, f"page_{page_number}.png")
            pix.save(image_path)
            
            return image_path
            
        finally:
            if 'doc' in locals():
                doc.close()
    
    def execute(self, pdf_file, start_page, end_page, output_folder):
        """Process a PDF file and extract pages as images"""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.TemporaryDirectory()
            pdf_path = os.path.join(self.temp_dir.name, "input.pdf")
            
            # Save uploaded file
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.getvalue())
            
            # Process each page
            image_paths = []
            for page_number in range(start_page, end_page + 1):
                self.log(f"Processing page {page_number}")
                image_path = self.extract_specific_page(pdf_path, page_number, output_folder)
                image_paths.append(image_path)
            
            return image_paths
            
        finally:
            if self.temp_dir:
                self.temp_dir.cleanup() 