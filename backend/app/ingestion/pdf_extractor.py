
from io import BytesIO

import pdfplumber
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_pdf_documents(
    pdf_content: bytes,
    source: str,
    user_id: str,
    pdf_hash: str,
) -> tuple[list[Document], str]:

    reader = PdfReader(BytesIO(pdf_content))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

    documents = []
    extracted_text_parts = []


    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""

        if page_text.strip():
            extracted_text_parts.append(page_text)

            chunks = splitter.split_text(page_text)

            for chunk_number, chunk in enumerate(chunks, start=1):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": source,
                            "pdf_hash": pdf_hash,
                            "user_id": user_id,
                            "page": page_number,
                            "chunk": chunk_number,
                            "content_type": "text",
                        },
                    )
                )

    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            for table_number, table in enumerate(tables, start=1):
                if not table:
                    continue

                table_rows=[]
                for row in table:
                    cells=[]
                    for cell in row:
                        if cell is not None:
                            cells.append(str(cell))
                        else:
                            cells.append("")
                    row_text="|".join(cells)
                    table_rows.append(row_text)
                table_text="\n".join(table_rows).strip()

                if not table_text:
                    continue

                documents.append(
                    Document(
                        page_content=(
                            f"Table {table_number} from page "
                            f"{page_number}:\n{table_text}"
                        ),
                        metadata={
                            "source": source,
                            "pdf_hash": pdf_hash,
                            "user_id": user_id,
                            "page": page_number,
                            "chunk": table_number,
                            "content_type": "table",
                            "table_number": table_number,
                        },
                    )
                )

    extracted_text = "\n\n".join(extracted_text_parts)

    return documents, extracted_text
