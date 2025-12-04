"""Email parsing utilities."""

import html
import re
from dataclasses import dataclass


@dataclass
class ParsedEmail:
    """Parsed email data."""

    subject: str
    body: str
    sender_email: str
    sender_name: str | None = None
    email_id: str | None = None


class EmailParser:
    """Parser for extracting email components."""

    @staticmethod
    def strip_html(html_content: str) -> str:
        """Strip HTML tags and decode entities.

        Args:
            html_content: HTML string to clean.

        Returns:
            Plain text content.
        """
        # Remove script and style elements
        text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode HTML entities
        text = html.unescape(text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format.

        Args:
            email: Email address to validate.

        Returns:
            True if valid, False otherwise.
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def extract_name_from_email(email: str) -> str | None:
        """Extract a display name from email format like 'Name <email@example.com>'.

        Args:
            email: Email string possibly containing display name.

        Returns:
            Extracted name or None.
        """
        match = re.match(r"^(.+?)\s*<[^>]+>$", email.strip())
        if match:
            return match.group(1).strip().strip('"').strip("'")
        return None

    @staticmethod
    def extract_email_address(email_string: str) -> str:
        """Extract email address from format like 'Name <email@example.com>'.

        Args:
            email_string: Email string possibly containing display name.

        Returns:
            Email address only.
        """
        match = re.search(r"<([^>]+)>", email_string)
        if match:
            return match.group(1)
        return email_string.strip()

    def parse(
        self,
        from_email: str,
        subject: str,
        body: str,
        sender_name: str | None = None,
        email_id: str | None = None,
    ) -> ParsedEmail:
        """Parse email input into structured format.

        Args:
            from_email: Sender email (may include display name).
            subject: Email subject.
            body: Email body (may be HTML).
            sender_name: Optional explicit sender name.
            email_id: Optional email tracking ID.

        Returns:
            ParsedEmail with cleaned data.

        Raises:
            ValueError: If email validation fails.
        """
        # Extract email address and optionally name
        email_address = self.extract_email_address(from_email)
        extracted_name = self.extract_name_from_email(from_email)

        # Validate email
        if not self.validate_email(email_address):
            raise ValueError(f"Invalid email address: {email_address}")

        # Clean body (strip HTML if present)
        clean_body = self.strip_html(body) if "<" in body and ">" in body else body.strip()

        # Clean subject
        clean_subject = self.strip_html(subject) if "<" in subject else subject.strip()

        # Use explicit name if provided, otherwise extracted name
        final_name = sender_name or extracted_name

        return ParsedEmail(
            subject=clean_subject,
            body=clean_body,
            sender_email=email_address,
            sender_name=final_name,
            email_id=email_id,
        )
