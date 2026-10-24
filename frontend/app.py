import hashlib
import uuid
import streamlit as st
from pypdf import PdfReader
from io import BytesIO
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.app.vectorstore.vectorstore import add_documents
from auth import (
    
    show_authentication,
    logout,
)

# Page configuration
st.set_page_config(
    page_title="StudyMate RAG",
    page_icon="📚",
    layout="wide"
)

if not show_authentication():
    st.stop()

# Logged-in user's application
st.title("📚 StudyMate RAG")
st.write("Your personal PDF question-answering assistant.")

# Show the current user and logout button
with st.sidebar:
    st.write("Logged in as:")
    st.write(st.session_state["user"]["email"])

    if st.button("Log out"):
        logout()


# PDF upload

# PDF upload
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
)

if uploaded_file is not None:
    pdf_content = uploaded_file.getvalue()

    # Identify the PDF using its actual contents.
    pdf_hash = hashlib.sha256(pdf_content).hexdigest()

    pdf_bytes = BytesIO(pdf_content)
    reader = PdfReader(pdf_bytes)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    documents = []
    extracted_text = ""

    # Extract text and create chunks from every page.
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        extracted_text += f"\n\n{page_text}"

        if not page_text.strip():
            continue

        page_chunks = splitter.split_text(page_text)

        for chunk_number, chunk in enumerate(page_chunks, start=1):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": uploaded_file.name,
                        "pdf_hash": pdf_hash,
                        "page": page_number,
                        "chunk": chunk_number,
                        "user_id": st.session_state["user"]["id"],
                    },
                )
            )

    # Generate a stable ID for every chunk.
    chunk_ids = []

    for document in documents:
        unique_key = (
            f"{document.metadata['user_id']}:"
            f"{document.metadata['pdf_hash']}:"
            f"{document.metadata['page']}:"
            f"{document.metadata['chunk']}"
        )

        chunk_id = str(
            uuid.uuid5(uuid.NAMESPACE_URL, unique_key)
        )

        chunk_ids.append(chunk_id)

    # Display extracted text and chunks.
    st.success("PDF uploaded successfully!")
    st.write("Total pages:", len(reader.pages))

    st.subheader("Extracted PDF Text")

    if extracted_text.strip():
        st.text_area(
            "PDF text",
            extracted_text,
            height=250,
        )

        st.subheader("Chunking Results")
        st.write("Total chunks:", len(documents))

        for index, document in enumerate(documents, start=1):
            with st.expander(f"Chunk {index}"):
                st.write(document.page_content)
                st.caption(
                    f"Page: {document.metadata['page']} | "
                    f"Characters: {len(document.page_content)}"
                )

        if st.button("Save PDF to Supabase"):
            try:
                with st.spinner("Creating embeddings and saving chunks..."):
                    stored_ids = add_documents(
                        documents=documents,
                        ids=chunk_ids,
                    )

                st.success(
                    f"Processed {len(stored_ids)} chunks successfully!"
                )

            except Exception as e:
                st.error(f"Failed to save PDF: {e}")

    else:
        st.warning("No readable text found in this PDF.")
