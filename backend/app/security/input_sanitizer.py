
import re


class InputSanitizer:
    """
    Checks user questions for common prompt-injection phrases.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"ignore\s+(all\s+)?above\s+instructions",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"show\s+(your\s+)?system\s+prompt",
        r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
        r"bypass\s+(all\s+)?safety\s+rules",
        r"disregard\s+(all\s+)?previous\s+instructions",
    ]

    @classmethod
    def check(cls, text: str) -> tuple[bool, str | None]:
        if not isinstance(text, str):
            return False, "Input must be text."

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return False, "Potential prompt injection detected."

        return True, None

    @staticmethod
    def clean(text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("Input must be a string.")

        return text.strip()
