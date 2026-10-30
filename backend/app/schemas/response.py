from pydantic import BaseModel,Field
class SourceReference(BaseModel):
    source:str =Field(
        description="Name of the source PDF file."
    )
    page:int | str=Field(
        description="Page number of the source PDF."
    )

class AnswerResponse(BaseModel):
    answer:str=Field(
        description="Answer generated using retrieved PDF content."
    )
    sources:list[SourceReference]=Field(
        default_factory=list,
        description="PDF sources supporting the answer."
    )