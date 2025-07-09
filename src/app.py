import os
import json
import tempfile

import streamlit as st
from dotenv import load_dotenv

from utils.file_handler import FileHandler
from agents.pdf_agent import PDFAgent
from agents.bengali_text_extraction_agent import BengaliTextExtractionAgent
from agents.hindi_text_extraction_agent import HindiTextExtractionAgent
from agents.mapping_agent import MappingAgent

# === Load environment ===
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# === Page config ===
st.set_page_config(
    page_title="Hindi↔Bengali PDF Mapper",
    page_icon="🔄",
    layout="wide",
)

st.title("🔄 Hindi ↔ Bengali PDF Sentence Mapper")
st.markdown("""
Upload a Hindi PDF and a Bengali PDF, select page ranges,  
and click **Process & Map** to auto-extract and align sentences.  
Only the final mappings are shown.  
""")

# — Upload & page selectors —
col1, col2 = st.columns(2)
with col1:
    st.subheader("📄 Hindi PDF")
    hindi_file = st.file_uploader("Upload Hindi PDF", type="pdf", key="hindi_pdf")
    hindi_start = st.number_input("Start Page", min_value=1, value=1, key="hindi_start")
    hindi_end = st.number_input("End Page", min_value=hindi_start, value=hindi_start, key="hindi_end")

with col2:
    st.subheader("📄 Bengali PDF")
    bengali_file = st.file_uploader("Upload Bengali PDF", type="pdf", key="bengali_pdf")
    bengali_start = st.number_input("Start Page", min_value=1, value=1, key="bengali_start")
    bengali_end = st.number_input("End Page", min_value=bengali_start, value=bengali_start, key="bengali_end")

# — Process & Map button —
if st.button("🚀 Process & Map"):
    # Validate inputs
    if not API_KEY:
        st.error("GEMINI_API_KEY not set in environment")
        st.stop()
    if not (hindi_file and bengali_file):
        st.error("Please upload both Hindi and Bengali PDFs.")
        st.stop()

    with st.spinner("Extracting and mapping…"):
        # 1) Extract pages from PDFs
        pdf_agent = PDFAgent()
        bengali_text_agent = BengaliTextExtractionAgent(API_KEY)
        hindi_text_agent = HindiTextExtractionAgent(API_KEY)
        mapping_agent = MappingAgent(API_KEY)

        # Hindi pages
        hindi_images = pdf_agent.execute(
            pdf_file=hindi_file,
            start_page=hindi_start,
            end_page=hindi_end,
            output_folder="hindi_pages"
        )
        hindi_pages = hindi_text_agent.execute(hindi_images)
        print("Hindi pages extracted:", hindi_pages)

        # Bengali pages
        bengali_images = pdf_agent.execute(
            pdf_file=bengali_file,
            start_page=bengali_start,
            end_page=bengali_end,
            output_folder="bengali_pages"
        )
        bengali_pages = bengali_text_agent.execute(bengali_images)
        print("Bengali pages extracted:", bengali_pages)

    # — Display extracted Hindi text —
    with st.expander("📝 Extracted Hindi Text", expanded=False):
        hindi_combined = ""
        for page in hindi_pages:
            page_no = page["page"]
            texts = page["texts"]
            st.markdown(f"**Page {page_no}:**")
            for sentence in texts:
                st.write(sentence)
            st.markdown("---")
            hindi_combined += f"Page {page_no}:\n" + "\n".join(texts) + "\n\n"

    # — Display extracted Bengali text —
    with st.expander("📝 Extracted Bengali Text", expanded=False):
        bengali_combined = ""
        for page in bengali_pages:
            page_no = page["page"]
            texts = page["texts"]
            st.markdown(f"**Page {page_no}:**")
            for sentence in texts:
                st.write(sentence)
            st.markdown("---")
            bengali_combined += f"Page {page_no}:\n" + "\n".join(texts) + "\n\n"

    # — Download buttons for extracted texts —
    st.download_button(
        label="🗕️ Download Extracted Hindi Text",
        data=hindi_combined,
        file_name="extracted_hindi.txt",
        mime="text/plain"
    )

    st.download_button(
        label="🗕️ Download Extracted Bengali Text",
        data=bengali_combined,
        file_name="extracted_bengali.txt",
        mime="text/plain"
    )

    with st.spinner("Running sentence mapping…"):
        page_mappings = mapping_agent.execute(hindi_pages, bengali_pages)

    # Display results side by side
    st.success("✅ Mapping complete!")
    for page_info in page_mappings:
        page_no = page_info["page"]
        with st.expander(f"📄 Page {page_no} Mappings", expanded=False):
            for m in page_info["mappings"]:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🇨🇳 Hindi**")
                    st.write(m["hindi"])
                with col2:
                    st.markdown("**🅱️ Bengali**")
                    st.write(m["bengali"])
                st.markdown("---")

    # — Download Mappings JSON —
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmp:
        json.dump(page_mappings, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        file_bytes = f.read()

    st.download_button(
        label="🗕️ Download Mappings (JSON)",
        data=file_bytes,
        file_name="sentence_mappings.json",
        mime="application/json"
    )
