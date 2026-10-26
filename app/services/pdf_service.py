import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class PDFReceiptGenerator:

    @staticmethod
    def generate_receipt_pdf(sale):
        """Generate a well-styled PDF invoice/receipt using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1b5e20'),
            alignment=1  # Center
        )
        subtitle_style = ParagraphStyle(
            'HeaderSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#555555'),
            alignment=1
        )
        meta_style = ParagraphStyle(
            'MetaText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#222222')
        )
        meta_bold = ParagraphStyle(
            'MetaBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#1b5e20')
        )

        # Header
        elements.append(Paragraph("GREENLEAF GROCERS", title_style))
        elements.append(Paragraph("Fresh Produce • Quality Groceries • Daily Essentials", subtitle_style))
        elements.append(Paragraph("104 Organic Way, Green Valley • Phone: (555) 321-4567", subtitle_style))
        elements.append(Spacer(1, 15))

        # Receipt Meta Info Table
        meta_data = [
            [
                Paragraph(f"<b>Invoice #:</b> {sale.invoice_no}", meta_style),
                Paragraph(f"<b>Date:</b> {sale.sale_date.strftime('%B %d, %Y')}", meta_style)
            ],
            [
                Paragraph(f"<b>Cashier:</b> {sale.cashier.full_name or sale.cashier.username if sale.cashier else 'System'}", meta_style),
                Paragraph(f"<b>Time:</b> {sale.sale_time.strftime('%I:%M %p')}", meta_style)
            ],
            [
                Paragraph(f"<b>Customer:</b> {sale.customer_name}", meta_style),
                Paragraph(f"<b>Payment:</b> {sale.payment_method}", meta_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[3.5 * inch, 3.5 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f9f4')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#c8e6c9')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # Items Table
        items_data = [["Item Description", "Unit Price", "Qty", "Total"]]
        for item in sale.items:
            items_data.append([
                item.product.name if item.product else 'Item',
                f"${item.price:.2f}",
                str(item.quantity),
                f"${item.subtotal:.2f}"
            ])

        items_table = Table(items_data, colWidths=[3.5 * inch, 1.2 * inch, 0.8 * inch, 1.5 * inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fcfcfc')])
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 12))

        # Financial Summary Table
        summary_data = [
            ["Subtotal:", f"${sale.subtotal:.2f}"],
            ["Discount:", f"-${sale.discount:.2f}"],
            ["Grand Total:", f"${sale.total_amount:.2f}"]
        ]
        summary_table = Table(summary_data, colWidths=[5.5 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1b5e20')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#1b5e20'))
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 25))

        # Footer
        elements.append(Paragraph("Thank you for shopping at GreenLeaf Grocers!", ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=11,
            textColor=colors.HexColor('#2e7d32'),
            alignment=1
        )))
        elements.append(Paragraph("Please retain this receipt for warranty and returns within 7 days.", subtitle_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer
