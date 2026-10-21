import streamlit as st
from pypdf import PdfReader
from io import BytesIO
st.set_page_config(
    page_title="StudyMate RAG",
    page_icon="📚",
    layout="wide"
)
st.title("📚 StudyMate RAG")
st.write("Your personal PDF question-answering assistant.")
uploaded_file=st.file_uploader(
    "Choose a PDF file",
    type=["pdf"]
)
if uploaded_file is not None:
    pdf_bytes=BytesIO(uploaded_file.getvalue())
    reader=PdfReader(pdf_bytes)
    st.success("PDF Uploaded Successfully!")
    st.write("Total pages:", len(reader.pages))
    extracted_text=""
    for page_number,page in enumerate(reader.pages,start=1):
        page_text=page.extract_text() or ""
        extracted_text += (
            f"\n---Page {page_number} ---\n"
            f"{page_text}\n"
        )
    st.subheader("Extracted PDF Text")
    if extracted_text.strip():
        st.text_area(
            "PDF content",
            value=extracted_text,
            height=400,
        )
    else:
        st.warning(
            "No readable text found."
            "This PDF may contain scanned images."
        )