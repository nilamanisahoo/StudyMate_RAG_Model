
import hashlib
import traceback
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from .dependencies import limiter, get_current_user_id
from ..ingestion.pdf_extractor import extract_pdf_documents
from ..ingestion.visual_analysis import analyze_all_pdf_pages
from ..vectorstore.vectorstore import replace_pdf_documents


router = APIRouter()

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/upload")
@limiter.limit("5/minute")
def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    processing_mode: str = Form("normal"),
    user_id: str = Depends(get_current_user_id),
):
    """Upload and process a PDF using the selected processing mode."""

    try:
        # 1. Validate processing mode.
        processing_mode = processing_mode.strip().lower()

        if processing_mode not in ["normal", "handwritten"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF processing mode.",
            )

        # 2. Validate filename.
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload a PDF file.",
            )

        # 3. Read PDF.
        pdf_content = file.file.read()

        if not pdf_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded PDF is empty.",
            )

        if len(pdf_content) > MAX_PDF_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="PDF size cannot exceed 20 MB.",
            )

        # 4. Validate PDF signature.
        if not pdf_content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is not a valid PDF.",
            )

        source = file.filename
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()

        print(f"Processing PDF: {source}")
        print(f"Processing mode: {processing_mode}")
        print(f"User ID: {user_id}")

        # 5. Extract text and tables.
        documents, extracted_text = extract_pdf_documents(
            pdf_content=pdf_content,
            source=source,
            user_id=user_id,
            pdf_hash=pdf_hash,
        )

        # 6. Run visual analysis only for handwritten PDFs.
        visual_documents = []
        failed_pages = []

        if processing_mode == "handwritten":

            print("Starting advanced visual analysis.")

            visual_documents, failed_pages = analyze_all_pdf_pages(
                pdf_content=pdf_content,
                source=source,
                user_id=user_id,
                pdf_hash=pdf_hash,
                dpi=150,
            )

        else:
            print("Normal PDF mode: skipping Gemini visual analysis.")

        # 7. Combine extracted documents.
        all_documents = documents + visual_documents

        if not all_documents:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "No searchable content could be extracted "
                    "from this PDF."
                ),
            )

        # 8. Generate stable document IDs.
        document_ids = []

        for document in all_documents:

            unique_key = (
                f"{user_id}:"
                f"{pdf_hash}:"
                f"{document.metadata['page']}:"
                f"{document.metadata['content_type']}:"
                f"{document.metadata['chunk']}"
            )

            document_id = str(
                uuid.uuid5(uuid.NAMESPACE_URL, unique_key)
            )

            document_ids.append(document_id)

        # 9. Generate embeddings and save to Supabase.
        stored_ids = replace_pdf_documents(
            documents=all_documents,
            ids=document_ids,
            user_id=user_id,
            pdf_hash=pdf_hash,
        )

        # 10. Return upload result.
        return {
            "message": "PDF uploaded and processed successfully.",
            "filename": source,
            "processing_mode": processing_mode,
            "pdf_hash": pdf_hash,
            "total_documents": len(stored_ids),
            "text_and_table_documents": len(documents),
            "visual_documents": len(visual_documents),
            "failed_visual_pages": failed_pages,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        print("PDF upload and processing failed.")
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "PDF processing failed. "
                "Please try again later."
            ),
        )
