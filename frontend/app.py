import streamlit as st
st.set_page_config(
    page_title="StudyMate RAG",
    page_icon="📚",
    layout="wide"
)
st.title("📚 StudyMate RAG")
st.write("Your personal PDF question-answering assistant.")
st.info(
    "Welcome! We will soon add PDF uploading,"
    "document processing, and AI-powered answers."
)
st.subheader("Project status")
st.success("StudyMate fronted is running!")
