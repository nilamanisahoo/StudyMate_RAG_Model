import re
class PIIDetector:
    PATTERNS={
    "email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),

    "phone": re.compile(
        r"(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\d[-.\s]?){9,12}\d(?!\w)"
    ),

    "credit_card": re.compile(
        r"\b(?:\d[ -]*?){13,19}\b"
    ),
    }
    MASK_MAP={
        "email": "[EMAIL REDACTED]",
        "phone": "[PHONE REDACTED]",
        "credit_card": "[CARD REDACTED]",
    }
    @classmethod
    def detect(cls,text:str)->list[str]:
        if not isinstance(text,str):
            raise TypeError("Input must be a string.")
        found={}
        for pii_type ,pattern in cls.PATTERNS.items():
           matches=pattern.findall(text)
           if matches:
               found[pii_type]=matches
        return found
    @classmethod
    def mask(cls,text:str)->str:
        if not isinstance(text,str):
            raise TypeError("Input must be a string.")
        masked=text
        for pii_type,pattern in cls.PATTERNS.items():
            masked=pattern.sub(cls.MASK_MAP[pii_type],masked)
        return masked