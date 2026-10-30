from backend.app.security.pii_detector import PIIDetector
class OutputValidator:
    @staticmethod
    def validate(text:str)->tuple[str,list[str]]:
        if not isinstance(text,str):
            raise TypeError("Output mmust be a string.")
        detected_pii=PIIDetector.detect(text)
        if not detected_pii:
            return text,[]
        cleaned_text=PIIDetector.mask(text)
        warnings=[
            f"Personal information detected: {pii_type}"
            for pii_type in detected_pii
        ]
        return cleaned_text,warnings
    