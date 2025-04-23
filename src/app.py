import streamlit as st
import os
from dotenv import load_dotenv
from pdf_processing.pdf_processor import PDFProcessor
from text_extraction.gemini_extractor import GeminiExtractor, TextParser
from utils.file_handler import FileHandler
import tempfile
import json
from google import genai

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="PDF Text Extractor",
    page_icon="📚",
    layout="wide"
)

# Title and description
st.title("📚 PDF Text Extractor")
st.markdown("""
This app extracts text from Hindi and Bengali PDF files using Google's Gemini AI. It can process specific page ranges and handle text in boxes.
""")

# Initialize session state for storing results
if 'hindi_results' not in st.session_state:
    st.session_state.hindi_results = {}
if 'bengali_results' not in st.session_state:
    st.session_state.bengali_results = {}

def process_pdf(pdf_file, start_page, end_page, api_key, output_folder):
    """Process a PDF file and extract text from specified pages"""
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded file
        pdf_path = os.path.join(temp_dir, "input.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.getvalue())
        
        # Initialize components
        pdf_processor = PDFProcessor(pdf_path)
        gemini_extractor = GeminiExtractor(api_key)
        file_handler = FileHandler()
        
        # Create output directory
        file_handler.ensure_directory_exists(output_folder)
        
        all_notes, all_texts = [], []
        
        try:
            # Process each page
            for page_number in range(start_page, end_page + 1):
                st.info(f"Processing page {page_number}...")
                
                # Extract page as image
                image_path = pdf_processor.extract_specific_page(page_number, output_folder)
                
                # Extract text using Gemini
                raw_text = gemini_extractor.extract_text(image_path)
                
                # Parse the extracted text
                notes, texts = TextParser.parse_sections(raw_text)
                all_notes.extend(notes)
                all_texts.extend(texts)
            
            return all_notes, all_texts
            
        finally:
            pdf_processor.close()

class SentenceMapper:
    def __init__(self, api_key):
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
            st.error(f"Error in mapping batch: {str(e)}")
            return []

def map_sentences(hindi_texts, bengali_texts, api_key, batch_size=10, overlap=2):
    """Map Hindi sentences to their Bengali translations using overlapping batches"""
    mapper = SentenceMapper(api_key)
    mappings = []
    seen_pairs = set()  # To track already mapped pairs
    
    # Process texts in overlapping batches
    for i in range(0, len(hindi_texts), batch_size - overlap):
        hindi_batch = hindi_texts[i:i + batch_size]
        bengali_batch = bengali_texts[i:i + batch_size]
        
        # Get mappings for this batch
        batch_mappings = mapper.map_batch(hindi_batch, bengali_batch)
        print(batch_mappings)
        # Add only new mappings
        raw = batch_mappings  # this is the str you printed
        # 1) Strip whitespace
        raw = raw.strip()

        # 2) If it starts/ends with a Markdown fence, remove those lines
        if raw.startswith("```"):
            lines = raw.splitlines()
            # drop the first line if it's a fence (``` or ```json)
            if lines[0].startswith("```"):
                lines.pop(0)
            # drop the last line if it's a fence
            if lines and lines[-1].startswith("```"):
                lines.pop(-1)
            raw = "\n".join(lines)

        # 3) Now raw should be pure JSON, so parse it
        batch_mappings = json.loads(raw)
        print(type(batch_mappings))
        for mapping in batch_mappings:
            print("mapping is ")
            print(mapping['hindi'])
            print(mapping['bengali'])
            pair_key = (mapping['hindi'], mapping['bengali'])
            print(pair_key)
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                mappings.append(mapping)
    
    return mappings

# Create two columns for Hindi and Bengali PDFs
col1, col2 = st.columns(2)

# Hindi PDF Section
with col1:
    st.subheader("Hindi PDF")
    hindi_file = st.file_uploader("Upload Hindi PDF", type=['pdf'], key="hindi")
    
    if hindi_file is not None:
        # Get page range for Hindi
        hindi_col1, hindi_col2 = st.columns(2)
        with hindi_col1:
            hindi_start = st.number_input("Start Page", min_value=1, value=1, key="hindi_start")
        with hindi_col2:
            hindi_end = st.number_input("End Page", min_value=hindi_start, value=hindi_start, key="hindi_end")
        
        # Process Hindi PDF button
        if st.button("Process Hindi PDF"):
            with st.spinner("Processing Hindi PDF..."):
                try:
                    # Get API key
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key:
                        st.error("GEMINI_API_KEY not found in environment variables")
                        st.stop()
                    
                    # Process the Hindi PDF
                    notes, texts = process_pdf(hindi_file, hindi_start, hindi_end, api_key, "gemini_hindi_output")
                    
                    # Store results in session state
                    st.session_state.hindi_results = {
                        'notes': notes,
                        'texts': texts
                    }
                    
                    st.success("Hindi PDF processing completed!")
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

# Bengali PDF Section
with col2:
    st.subheader("Bengali PDF")
    bengali_file = st.file_uploader("Upload Bengali PDF", type=['pdf'], key="bengali")
    
    if bengali_file is not None:
        # Get page range for Bengali
        bengali_col1, bengali_col2 = st.columns(2)
        with bengali_col1:
            bengali_start = st.number_input("Start Page", min_value=1, value=1, key="bengali_start")
        with bengali_col2:
            bengali_end = st.number_input("End Page", min_value=bengali_start, value=bengali_start, key="bengali_end")
        
        # Process Bengali PDF button
        if st.button("Process Bengali PDF"):
            with st.spinner("Processing Bengali PDF..."):
                try:
                    # Get API key
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key:
                        st.error("GEMINI_API_KEY not found in environment variables")
                        st.stop()
                    
                    # Process the Bengali PDF
                    notes, texts = process_pdf(bengali_file, bengali_start, bengali_end, api_key, "gemini_bengali_output")
                    
                    # Store results in session state
                    st.session_state.bengali_results = {
                        'notes': notes,
                        'texts': texts
                    }
                    
                    st.success("Bengali PDF processing completed!")
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

# Display results if available
if st.session_state.hindi_results or st.session_state.bengali_results:
    st.markdown("---")
    st.subheader("Extracted Text")
    
    # Create tabs for Hindi and Bengali results
    tab1, tab2, tab3 = st.tabs(["Hindi Results", "Bengali Results", "Sentence Mapping"])
    
    # Hindi Results
    with tab1:
        if st.session_state.hindi_results:
            st.markdown("### Hindi PDF Results")
            hindi_tab1, hindi_tab2 = st.tabs(["Notes", "Texts"])
            
            with hindi_tab1:
                st.markdown("#### Notes (Text from boxes)")
                for note in st.session_state.hindi_results['notes']:
                    st.text(note)
            
            with hindi_tab2:
                st.markdown("#### Texts (Regular content)")
                for text in st.session_state.hindi_results['texts']:
                    st.text(text)
            
            # Download Hindi results
            if st.button("Download Hindi Results"):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
                    tmp.write(b"**NOTES:**\n")
                    tmp.write("\n".join(st.session_state.hindi_results['notes']).encode())
                    tmp.write(b"\n\n**TEXTS:**\n")
                    tmp.write("\n".join(st.session_state.hindi_results['texts']).encode())
                    
                    with open(tmp.name, 'rb') as f:
                        st.download_button(
                            label="Download Hindi Results",
                            data=f,
                            file_name="hindi_extracted_text.txt",
                            mime="text/plain"
                        )
        else:
            st.info("No Hindi PDF processed yet")
    
    # Bengali Results
    with tab2:
        if st.session_state.bengali_results:
            st.markdown("### Bengali PDF Results")
            bengali_tab1, bengali_tab2 = st.tabs(["Notes", "Texts"])
            
            with bengali_tab1:
                st.markdown("#### Notes (Text from boxes)")
                for note in st.session_state.bengali_results['notes']:
                    st.text(note)
            
            with bengali_tab2:
                st.markdown("#### Texts (Regular content)")
                for text in st.session_state.bengali_results['texts']:
                    st.text(text)
            
            # Download Bengali results
            if st.button("Download Bengali Results"):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
                    tmp.write(b"**NOTES:**\n")
                    tmp.write("\n".join(st.session_state.bengali_results['notes']).encode())
                    tmp.write(b"\n\n**TEXTS:**\n")
                    tmp.write("\n".join(st.session_state.bengali_results['texts']).encode())
                    
                    with open(tmp.name, 'rb') as f:
                        st.download_button(
                            label="Download Bengali Results",
                            data=f,
                            file_name="bengali_extracted_text.txt",
                            mime="text/plain"
                        )
        else:
            st.info("No Bengali PDF processed yet")
    
    # Sentence Mapping
    with tab3:
        if st.session_state.hindi_results and st.session_state.bengali_results:
            st.markdown("### Sentence Mapping")
            
            if st.button("Generate Sentence Mapping"):
                with st.spinner("Generating sentence mappings..."):
                    try:
                        # Get API key
                        api_key = os.getenv("GEMINI_API_KEY")
                        if not api_key:
                            st.error("GEMINI_API_KEY not found in environment variables")
                            st.stop()
                        
                        # Get texts from both languages
                        hindi_texts = st.session_state.hindi_results['texts']
                        bengali_texts = st.session_state.bengali_results['texts']
                        
                        # Generate mappings
                        mappings = map_sentences(hindi_texts, bengali_texts, api_key)
                        
                        # Display mappings
                        for mapping in mappings:
                            st.markdown("---")
                            st.markdown("**Hindi:**")
                            st.text(mapping['hindi'])
                            st.markdown("**Bengali:**")
                            st.text(mapping['bengali'])
                        
                        # Download mappings
                        if st.button("Download Mappings"):
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
                                json.dump(mappings, tmp, ensure_ascii=False, indent=2)
                                
                                with open(tmp.name, 'rb') as f:
                                    st.download_button(
                                        label="Download Sentence Mappings",
                                        data=f,
                                        file_name="sentence_mappings.json",
                                        mime="application/json"
                                    )
                    except Exception as e:
                        st.error(f"An error occurred during mapping: {str(e)}")
        else:
            st.info("Process both Hindi and Bengali PDFs to generate sentence mappings") 