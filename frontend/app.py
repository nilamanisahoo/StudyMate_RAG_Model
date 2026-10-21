import streamlit as st
from pypdf import PdfReader
from io import BytesIO
from langchain_text_splitters import RecursiveCharacterTextSplitter
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
            f"{page_text}\n"
        )
    st.subheader("Extracted PDF Text")
    if extracted_text.strip():
       splitter=RecursiveCharacterTextSplitter(
           chunk_size=500,
           chunk_overlap=50,
       )
       chunks=splitter.split_text(extracted_text)
       st.subheader("Chunking Results")
       st.write("Total chunks:", len(chunks))
       for index,chunk in enumerate(chunks,start=1):
           with st.expander(f"Chunk {index}"):
               st.write(chunk)
               st.caption(f"Characters: {len(chunk)}")
    else:
        st.warning("No readable text found in this PDF.")