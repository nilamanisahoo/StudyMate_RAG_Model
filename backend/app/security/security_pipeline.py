from backend.app.security.input_sanitizer import InputSanitizer
from backend.app.security.pii_detector import PIIDetector
from backend.app.security.output_validator import OutputValidator

class SecurityPipeline:
    @staticmethod
    def process_input(text: str) -> tuple[str, list[str]]:

        # Step 1: Check input for prompt injection
        is_safe, warning = InputSanitizer.check(text)

        if not is_safe:
            raise ValueError(warning)

        # Step 2: Remove unnecessary spaces
        cleaned_text = InputSanitizer.clean(text)

        # Step 3: Detect and mask PII
        cleaned_text = PIIDetector.mask(cleaned_text)

        return cleaned_text, []

    @staticmethod
    def process_output(text: str) -> tuple[str, list[str]]:

        # Validate AI-generated answer
        cleaned_text, warnings = OutputValidator.validate(text)

        return cleaned_text, warnings