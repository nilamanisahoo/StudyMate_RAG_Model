from io import BytesIO
import pymupdf

def render_pdf_pages(
        pdf_content:bytes,
        page_numbers:list[int] | None=None,
        dpi:int=120,
)-> list[dict]:
    if dpi<1:
        raise ValueError("dpi must be greater than 0.")
    pdf=pymupdf.open(
        stream=pdf_content,
        filetype="pdf"
    )
    try:
        if page_numbers is None:
            selected_pages=range(len(pdf))
        else:
            selected_pages=[]
            for page_number in page_numbers:
                if page_number<1 or page_number>len(pdf):
                    raise ValueError(f"Invalid PDF page number: {page_number}")
                selected_pages.append(page_number-1)
        render_pages=[]
        for page_index in selected_pages:
            page=pdf[page_index]
            zoom=dpi/72
            matrix=pymupdf.Matrix(zoom,zoom)
            pixmap=page.get_pixmap(
                matrix=matrix,
                alpha=False
            )
            image_bytes=pixmap.tobytes("png")
            render_pages.append(
                {
                    "page":page_index+1,
                    "image":image_bytes,
                    "content_type":"image/png"
                }
            )
        return render_pages
    finally:
        pdf.close()
        