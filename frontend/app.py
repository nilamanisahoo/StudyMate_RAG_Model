
import hashlib
import uuid
from time import perf_counter
import streamlit as st

from backend.app.ingestion.pdf_extractor import extract_pdf_documents
from backend.app.ingestion.visual_analysis import analyze_all_pdf_pages
from backend.app.vectorstore.vectorstore import replace_pdf_documents
from auth import show_authentication, logout
st.set_page_config(
    page_title="StudyMate RAG",
    page_icon="📚",
    layout="wide",
)

# Require login before showing the application.
if not show_authentication():
    st.stop()


st.title("📚 StudyMate RAG")
st.write("Your personal PDF question-answering assistant.")

# Sidebar: logged-in user and logout.
with st.sidebar:
    st.write("Logged in as:")
    st.write(st.session_state["user"]["email"])

    if st.button("Log out"):
        logout()


# Upload a PDF.
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
)

if uploaded_file is not None:
    pdf_content = uploaded_file.getvalue()

    # Identify the exact PDF content.
    pdf_hash = hashlib.sha256(pdf_content).hexdigest()
    user_id = st.session_state["user"]["id"]
    st.write("Current user ID:", user_id)

    # Extract text and tables using our separate module.
    try:
        with st.spinner("Extracting PDF text and tables..."):
            documents, extracted_text = extract_pdf_documents(
                pdf_content=pdf_content,
                source=uploaded_file.name,
                user_id=user_id,
                pdf_hash=pdf_hash,
            )

    except Exception as e:
        st.error(f"PDF extraction failed: {e}")
        st.stop()

    st.success("PDF extraction completed!")

    st.write("Total chunks and tables:", len(documents))

    # Display extracted text.
    st.subheader("Extracted PDF Text")

    if extracted_text.strip():
        st.text_area(
            "PDF text",
            extracted_text,
            height=250,
        )
    else:
        st.info("No selectable text was extracted from this PDF.")

    # Display text chunks and table documents.
    st.subheader("Extraction Results")

    text_count = sum(
        doc.metadata.get("content_type") == "text"
        for doc in documents
    )

    table_count = sum(
        doc.metadata.get("content_type") == "table"
        for doc in documents
    )

    col1, col2 = st.columns(2)
    col1.metric("Text chunks", text_count)
    col2.metric("Tables", table_count)

    for index, document in enumerate(documents, start=1):
        content_type = document.metadata.get("content_type", "text")
        page_number = document.metadata.get("page", "?")

        with st.expander(
            f"{content_type.title()} {index} — Page {page_number}"
        ):
            st.write(document.page_content)
            st.caption(f"Type: {content_type} | Page: {page_number}")

 
    # Save text, table, and visual documents to Supabase.
    if documents:
        if st.button("Save PDF to Supabase"):
            start_time = perf_counter()        
            try:
                with st.spinner(
                    "Analyzing every PDF page for graphs, diagrams, "
                    "images, and handwriting..."
                ):
                    visual_documents, failed_pages = analyze_all_pdf_pages(
                        pdf_content=pdf_content,
                        source=uploaded_file.name,
                        user_id=user_id,
                        pdf_hash=pdf_hash,
                        dpi=150,
                    )

                # Combine text, tables, and visual descriptions.
                all_documents = documents + visual_documents

                # Generate deterministic IDs for all documents.
                chunk_ids = []

                for document in all_documents:
                    unique_key = (
                        f"{user_id}:"
                        f"{pdf_hash}:"
                        f"{document.metadata['page']}:"
                        f"{document.metadata['content_type']}:"
                        f"{document.metadata['chunk']}"
                    )

                    chunk_id = str(
                        uuid.uuid5(uuid.NAMESPACE_URL, unique_key)
                    )
                    chunk_ids.append(chunk_id)

                with st.spinner(
                    "Creating embeddings and saving all documents..."
                ):
                    stored_ids = replace_pdf_documents(
                        documents=all_documents,
                        ids=chunk_ids,
                        user_id=user_id,
                        pdf_hash=pdf_hash,
                    )

                st.success(
                    f"Saved {len(stored_ids)} documents successfully!"
                )
                elapsed_time = perf_counter() - start_time
                st.info(f"Total PDF processing and saving time: {elapsed_time:.2f} seconds")
                st.write("Text and table documents:", len(documents))
                st.write("Visual documents:", len(visual_documents))

                if failed_pages:
                    st.warning(
                        f"Visual analysis failed for pages: {failed_pages}"
                    )
                else:
                    st.success(
                        "Visual analysis succeeded for every page."
                    )

            except Exception as e:
                st.error(f"Failed to process or save PDF: {e}")

    else:
        st.warning(
            "No selectable text or tables were extracted. "
            "Scanned PDFs may still contain useful visual information, "
            "but this save workflow currently requires at least one "
            "text or table document."
        )
