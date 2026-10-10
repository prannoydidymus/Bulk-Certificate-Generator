import os
from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors


class CertificateTemplateGenerator:
    """Predefined professional certificate template generator using ReportLab."""

    def __init__(self):
        self.width, self.height = landscape(A4)

    def generate_pdf(
        self,
        output_path: str,
        recipient_name: str,
        event_name: str,
        organization_name: str,
        issue_date: str,
        signatory_name: str,
        signatory_title: str,
        certificate_code: str,
        custom_note: str | None = None,
    ) -> str:
        """
        Generates a PDF certificate file for a given recipient.
        
        Args:
            output_path: Path where the PDF should be saved.
            recipient_name: Name of the recipient.
            event_name: Event or course title.
            organization_name: Issuing organization.
            issue_date: Formatted issue date.
            signatory_name: Authorized person name.
            signatory_title: Signatory title.
            certificate_code: Unique certificate identifier.
            custom_note: Optional special remark or achievement note.
            
        Returns:
            The output path of the generated PDF file.
        """
        parent_dir = Path(output_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(output_path, pagesize=(self.width, self.height))
        w, h = self.width, self.height

        # Colors
        primary_navy = colors.HexColor("#0F172A")
        gold_accent = colors.HexColor("#D97706")
        light_gold = colors.HexColor("#FDE68A")
        subtext_slate = colors.HexColor("#475569")
        cream_bg = colors.HexColor("#FDFBF7")

        # 1. Background fill
        c.setFillColor(cream_bg)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # 2. Outer Navy Border
        c.setStrokeColor(primary_navy)
        c.setLineWidth(4)
        c.rect(25, 25, w - 50, h - 50, fill=0, stroke=1)

        # 3. Inner Gold Border
        c.setStrokeColor(gold_accent)
        c.setLineWidth(1.5)
        c.rect(33, 33, w - 66, h - 66, fill=0, stroke=1)

        # 4. Corner Ornaments
        self._draw_corner_accents(c, 33, 33, w - 66, h - 66, gold_accent)

        # 5. Organization Header
        c.setFillColor(primary_navy)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(w / 2, h - 75, organization_name.upper())

        # Header underline
        c.setStrokeColor(gold_accent)
        c.setLineWidth(1)
        c.line(w / 2 - 120, h - 82, w / 2 + 120, h - 82)

        # 6. Main Certificate Title
        c.setFillColor(primary_navy)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(w / 2, h - 130, "CERTIFICATE OF COMPLETION")

        # 7. Presentation Subtitle
        c.setFillColor(subtext_slate)
        c.setFont("Helvetica", 12)
        c.drawCentredString(w / 2, h - 165, "THIS IS PROUDLY PRESENTED TO")

        # 8. Recipient Name (Prominent & Elegant)
        c.setFillColor(primary_navy)
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(w / 2, h - 215, recipient_name)

        # Decorative gold underline for recipient name
        name_width = min(c.stringWidth(recipient_name, "Helvetica-Bold", 30) + 40, w - 160)
        c.setStrokeColor(gold_accent)
        c.setLineWidth(2)
        c.line(w / 2 - name_width / 2, h - 225, w / 2 + name_width / 2, h - 225)

        # 9. Completion Citation
        c.setFillColor(subtext_slate)
        c.setFont("Helvetica", 12)
        c.drawCentredString(w / 2, h - 265, "for successfully completing all requirements for")

        # 10. Event / Course Name
        c.setFillColor(primary_navy)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(w / 2, h - 305, event_name)

        # Optional custom note
        if custom_note and custom_note.strip():
            c.setFillColor(subtext_slate)
            c.setFont("Helvetica-Oblique", 11)
            c.drawCentredString(w / 2, h - 335, f"Special Distinction: {custom_note.strip()}")

        # 11. Footer Section
        footer_y = 100

        # Left: Date of Issue
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(1)
        c.line(80, footer_y + 35, 230, footer_y + 35)

        c.setFillColor(primary_navy)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(80, footer_y + 18, issue_date)

        c.setFillColor(subtext_slate)
        c.setFont("Helvetica", 9)
        c.drawString(80, footer_y + 5, "DATE OF ISSUANCE")

        # Center: Gold Official Seal
        self._draw_seal(c, w / 2, footer_y + 25, gold_accent, light_gold, primary_navy)

        # Verification Code
        c.setFillColor(subtext_slate)
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, footer_y - 25, f"CERTIFICATE ID: {certificate_code}")

        # Right: Signatory
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(1)
        c.line(w - 230, footer_y + 35, w - 80, footer_y + 35)

        # Stylized faux signature
        c.setFillColor(colors.HexColor("#1E3A8A"))
        c.setFont("Times-BoldItalic", 14)
        c.drawString(w - 230, footer_y + 40, signatory_name)

        c.setFillColor(primary_navy)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(w - 230, footer_y + 18, signatory_name)

        c.setFillColor(subtext_slate)
        c.setFont("Helvetica", 9)
        c.drawString(w - 230, footer_y + 5, signatory_title.upper())

        c.save()
        return output_path

    def _draw_corner_accents(self, c, x, y, width, height, color):
        """Draw decorative corner corner accents inside inner border."""
        c.setStrokeColor(color)
        c.setLineWidth(1.5)
        offset = 12
        bracket_len = 16

        # Top-left
        c.line(x + offset, y + height - offset, x + offset + bracket_len, y + height - offset)
        c.line(x + offset, y + height - offset, x + offset, y + height - offset - bracket_len)

        # Top-right
        c.line(x + width - offset, y + height - offset, x + width - offset - bracket_len, y + height - offset)
        c.line(x + width - offset, y + height - offset, x + width - offset, y + height - offset - bracket_len)

        # Bottom-left
        c.line(x + offset, y + offset, x + offset + bracket_len, y + offset)
        c.line(x + offset, y + offset, x + offset, y + offset + bracket_len)

        # Bottom-right
        c.line(x + width - offset, y + offset, x + width - offset - bracket_len, y + offset)
        c.line(x + width - offset, y + offset, x + width - offset, y + offset + bracket_len)

    def _draw_seal(self, c, cx, cy, border_color, fill_color, text_color):
        """Draw an official circular badge seal."""
        c.setFillColor(fill_color)
        c.setStrokeColor(border_color)
        c.setLineWidth(2)
        c.circle(cx, cy, 28, fill=1, stroke=1)

        c.setLineWidth(1)
        c.circle(cx, cy, 24, fill=0, stroke=1)

        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx, cy + 6, "OFFICIAL")
        c.drawCentredString(cx, cy - 2, "★ SEAL ★")
        c.drawCentredString(cx, cy - 10, "VERIFIED")
