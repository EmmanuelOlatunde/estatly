# documents/generators.py

"""
PDF generation logic for different document types.

This module contains the actual PDF creation logic that was missing.
It integrates with the existing document management infrastructure.
"""

import logging
from io import BytesIO
from datetime import datetime
# from typing import Dict, Any
# from uuid import UUID

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors

from .models import Document, DocumentType

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Base class for PDF generation."""
    
    def __init__(self, document: Document):
        self.document = document
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
        )
    
    def generate(self) -> bytes:
        """
        Generate PDF and return bytes.
        
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement generate()")


class PaymentReceiptGenerator(PDFGenerator):
    """Generator for payment receipt PDFs."""
    
    def generate(self) -> bytes:
        """Generate payment receipt PDF."""
        logger.info(f"Generating payment receipt for document {self.document.id}")
        
        # Get payment data from metadata
        metadata = self.document.metadata or {}
        
        # Create PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            title=self.document.title, 
            author="Estatly",  
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("PAYMENT RECEIPT", self.title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Receipt info
        receipt_info = [
            [
                Paragraph(f"<b>Receipt No:</b> {metadata.get('receipt_number', 'N/A')}", self.normal_style),
                Paragraph(f"<b>Date:</b> {self.document.created_at.strftime('%B %d, %Y')}", self.normal_style)
            ]
        ]
        receipt_table = Table(receipt_info, colWidths=[3.5*inch, 3.5*inch])
        receipt_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(receipt_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Property details
        elements.append(Paragraph("PROPERTY DETAILS", self.heading_style))
        property_data = [
            ["Estate:", metadata.get('estate_name', 'N/A')],
            ["Unit:", metadata.get('unit_identifier', 'N/A')],
        ]
        property_table = Table(property_data, colWidths=[1.5*inch, 5.5*inch])
        property_table.setStyle(self._get_table_style())
        elements.append(property_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Payment details
        elements.append(Paragraph("PAYMENT DETAILS", self.heading_style))
        payment_data = [
            ["Fee Name:", metadata.get('fee_name', 'N/A')],
            ["Payment Method:", metadata.get('payment_method', 'N/A').replace('_', ' ').title()],
            ["Payment Date:", metadata.get('payment_date', 'N/A')],
        ]
        payment_table = Table(payment_data, colWidths=[1.5*inch, 5.5*inch])
        payment_table.setStyle(self._get_table_style())
        elements.append(payment_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Amount box
        amount = metadata.get('amount', 0)
        amount_text = f"₦{float(amount):,.2f}"
        amount_data = [
            [Paragraph("<b>AMOUNT PAID</b>", self.normal_style)],
            [Paragraph(f"<font size=20><b>{amount_text}</b></font>", self.normal_style)],
        ]
        amount_table = Table(amount_data, colWidths=[7*inch])
        amount_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
            ('BORDER', (0, 0), (-1, -1), 2, colors.HexColor('#0ea5e9')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(amount_table)
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(
            "This is an official receipt generated electronically.",
            footer_style
        ))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Return bytes
        pdf_bytes = self.buffer.getvalue()
        logger.info(f"Payment receipt generated: {len(pdf_bytes)} bytes")
        return pdf_bytes
    
    def _get_table_style(self):
        """Standard table style for receipt tables."""
        return TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])


class AnnouncementGenerator(PDFGenerator):
    """Generator for announcement PDFs."""
    
    def generate(self) -> bytes:
        """Generate announcement PDF."""
        logger.info(f"Generating announcement for document {self.document.id}")
        
        metadata = self.document.metadata or {}
        
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            title=self.document.title, 
            author="Estatly",  
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("ANNOUNCEMENT", self.title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Announcement title
        title = metadata.get('announcement_title', self.document.title)
        elements.append(Paragraph(f"<b>{title}</b>", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Content
        content = metadata.get('content', 'No content available')
        content_para = Paragraph(content, self.normal_style)
        elements.append(content_para)
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(
            f"Issued on {self.document.created_at.strftime('%B %d, %Y')}",
            footer_style
        ))
        
        doc.build(elements)
        
        pdf_bytes = self.buffer.getvalue()
        logger.info(f"Announcement generated: {len(pdf_bytes)} bytes")
        return pdf_bytes


def generate_document_pdf_content(document: Document) -> bytes:
    """
    Generate PDF content for a document based on its type.
    
    This is the MISSING PIECE that creates the actual PDF bytes.
    
    Args:
        document: Document instance to generate PDF for
    
    Returns:
        PDF content as bytes
    
    Raises:
        ValueError: If document type is not supported
    """
    logger.info(f"Generating PDF for document {document.id}, type={document.document_type}")
    
    generators = {
        DocumentType.PAYMENT_RECEIPT: PaymentReceiptGenerator,
        DocumentType.ANNOUNCEMENT: AnnouncementGenerator,
    }
    
    generator_class = generators.get(document.document_type)
    
    if not generator_class:
        raise ValueError(f"Unsupported document type: {document.document_type}")
    
    generator = generator_class(document)
    return generator.generate()