"""
Generate a synthetic credit report PDF for testing CreditSense.
Mimics the structure of a real US credit report (Experian-style).
All data is fictional.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "sample_reports", "sample_credit_report.pdf")


def build_report():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a3c6e"),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a3c6e"),
        spaceBefore=16,
        spaceAfter=8,
        borderWidth=1,
        borderColor=colors.HexColor("#1a3c6e"),
        borderPadding=4,
    ))
    styles.add(ParagraphStyle(
        name="SubHeader",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=colors.HexColor("#333333"),
        spaceBefore=10,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="FieldLabel",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#666666"),
    ))
    styles.add(ParagraphStyle(
        name="FieldValue",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#000000"),
    ))
    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#888888"),
    ))

    elements = []

    # ===== HEADER =====
    elements.append(Paragraph("EXPERIAN", styles["ReportTitle"]))
    elements.append(Paragraph("Consumer Credit Report", styles["Heading3"]))
    elements.append(Paragraph("Report Date: January 15, 2026 &nbsp;&nbsp;|&nbsp;&nbsp; Report Number: EXP-2026-8847231", styles["SmallText"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3c6e"), spaceAfter=12))

    # ===== PERSONAL INFORMATION =====
    elements.append(Paragraph("PERSONAL INFORMATION", styles["SectionHeader"]))

    personal_data = [
        ["Name:", "JOHN MICHAEL ANDERSON", "Date of Birth:", "03/15/1988"],
        ["Current Address:", "4521 Oak Ridge Drive, Apt 12B", "SSN:", "XXX-XX-4832"],
        ["", "Austin, TX 78745", "Phone:", "(512) 555-0147"],
        ["Previous Address:", "1893 Maple Avenue", "Employer:", "TechFlow Solutions Inc."],
        ["", "Houston, TX 77002", "Position:", "Senior Software Engineer"],
    ]

    personal_table = Table(personal_data, colWidths=[1.3 * inch, 2.5 * inch, 1.1 * inch, 2.1 * inch])
    personal_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("FONT", (1, 0), (1, -1), "Helvetica", 9),
        ("FONT", (3, 0), (3, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(personal_table)

    # ===== CREDIT SCORE =====
    elements.append(Paragraph("CREDIT SCORE SUMMARY", styles["SectionHeader"]))

    score_data = [
        ["FICO\u00ae Score 8", "Score Range", "Risk Level", "Score Date"],
        ["680", "300 - 850", "Fair", "January 15, 2026"],
    ]

    score_table = Table(score_data, colWidths=[1.75 * inch, 1.75 * inch, 1.75 * inch, 1.75 * inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONT", (0, 1), (0, 1), "Helvetica-Bold", 18),
        ("TEXTCOLOR", (0, 1), (0, 1), colors.HexColor("#d4760a")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 8))

    # Score factors
    elements.append(Paragraph("Key Factors Affecting Your Score:", styles["SubHeader"]))
    factors = [
        "1. Proportion of balances to credit limits is too high on revolving accounts (Credit Utilization: 72%)",
        "2. One or more accounts with a late payment (30-day late payment reported June 2025, Chase Visa account)",
        "3. Length of credit history is too short (Average account age: 2.3 years)",
        "4. Too many recent inquiries in the last 12 months (5 hard inquiries)",
        "5. Limited mix of credit types (primarily revolving credit, no installment loans)",
    ]
    for f in factors:
        elements.append(Paragraph(f, styles["FieldValue"]))
        elements.append(Spacer(1, 3))

    # ===== ACCOUNT INFORMATION =====
    elements.append(Paragraph("ACCOUNT INFORMATION", styles["SectionHeader"]))
    elements.append(Paragraph("Total Accounts: 6 &nbsp;&nbsp;|&nbsp;&nbsp; Open Accounts: 5 &nbsp;&nbsp;|&nbsp;&nbsp; Closed Accounts: 1", styles["FieldValue"]))
    elements.append(Spacer(1, 8))

    # Account 1
    elements.append(Paragraph("CHASE VISA PLATINUM", styles["SubHeader"]))
    acct1 = [
        ["Account Number:", "XXXX-XXXX-XXXX-4521", "Account Type:", "Revolving Credit Card"],
        ["Date Opened:", "March 2022", "Credit Limit:", "$8,500"],
        ["Current Balance:", "$6,120", "Monthly Payment:", "$185"],
        ["Payment Status:", "30 Days Late (June 2025)", "High Balance:", "$7,200"],
        ["Account Status:", "Open / Current", "Last Reported:", "January 2026"],
    ]
    acct1_table = Table(acct1, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
    acct1_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8),
        ("FONT", (1, 0), (1, -1), "Helvetica", 8),
        ("FONT", (3, 0), (3, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    elements.append(acct1_table)
    elements.append(Spacer(1, 4))

    # Payment History Grid for Account 1
    elements.append(Paragraph("Payment History (Last 12 Months):", styles["FieldLabel"]))
    months_header = ["Jan 26", "Dec 25", "Nov 25", "Oct 25", "Sep 25", "Aug 25",
                     "Jul 25", "Jun 25", "May 25", "Apr 25", "Mar 25", "Feb 25"]
    payment_status = ["OK", "OK", "OK", "OK", "OK", "OK", "OK", "30", "OK", "OK", "OK", "OK"]
    payment_grid = Table([months_header, payment_status],
                         colWidths=[0.583 * inch] * 12)
    payment_grid.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica", 6),
        ("FONT", (0, 1), (-1, 1), "Helvetica-Bold", 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BACKGROUND", (7, 1), (7, 1), colors.HexColor("#ffcccc")),  # June 2025 late
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(payment_grid)
    elements.append(Spacer(1, 10))

    # Account 2
    elements.append(Paragraph("CAPITAL ONE QUICKSILVER", styles["SubHeader"]))
    acct2 = [
        ["Account Number:", "XXXX-XXXX-XXXX-7893", "Account Type:", "Revolving Credit Card"],
        ["Date Opened:", "August 2023", "Credit Limit:", "$5,000"],
        ["Current Balance:", "$3,200", "Monthly Payment:", "$95"],
        ["Payment Status:", "Current - Paid as Agreed", "High Balance:", "$4,100"],
        ["Account Status:", "Open / Current", "Last Reported:", "January 2026"],
    ]
    acct2_table = Table(acct2, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
    acct2_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8),
        ("FONT", (1, 0), (1, -1), "Helvetica", 8),
        ("FONT", (3, 0), (3, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    elements.append(acct2_table)
    elements.append(Spacer(1, 10))

    # Account 3
    elements.append(Paragraph("DISCOVER IT CASH BACK", styles["SubHeader"]))
    acct3 = [
        ["Account Number:", "XXXX-XXXX-XXXX-2156", "Account Type:", "Revolving Credit Card"],
        ["Date Opened:", "January 2024", "Credit Limit:", "$3,000"],
        ["Current Balance:", "$1,450", "Monthly Payment:", "$50"],
        ["Payment Status:", "Current - Paid as Agreed", "High Balance:", "$2,800"],
        ["Account Status:", "Open / Current", "Last Reported:", "January 2026"],
    ]
    acct3_table = Table(acct3, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
    acct3_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8),
        ("FONT", (1, 0), (1, -1), "Helvetica", 8),
        ("FONT", (3, 0), (3, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    elements.append(acct3_table)
    elements.append(Spacer(1, 10))

    # Account 4
    elements.append(Paragraph("AMAZON STORE CARD (SYNCHRONY)", styles["SubHeader"]))
    acct4 = [
        ["Account Number:", "XXXX-XXXX-XXXX-9034", "Account Type:", "Revolving Charge Card"],
        ["Date Opened:", "November 2023", "Credit Limit:", "$2,500"],
        ["Current Balance:", "$780", "Monthly Payment:", "$35"],
        ["Payment Status:", "Current - Paid as Agreed", "High Balance:", "$1,900"],
        ["Account Status:", "Open / Current", "Last Reported:", "December 2025"],
    ]
    acct4_table = Table(acct4, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
    acct4_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8),
        ("FONT", (1, 0), (1, -1), "Helvetica", 8),
        ("FONT", (3, 0), (3, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    elements.append(acct4_table)
    elements.append(Spacer(1, 10))

    # Account 5
    elements.append(Paragraph("CITI DOUBLE CASH", styles["SubHeader"]))
    acct5 = [
        ["Account Number:", "XXXX-XXXX-XXXX-6177", "Account Type:", "Revolving Credit Card"],
        ["Date Opened:", "June 2024", "Credit Limit:", "$4,000"],
        ["Current Balance:", "$2,100", "Monthly Payment:", "$65"],
        ["Payment Status:", "Current - Paid as Agreed", "High Balance:", "$3,500"],
        ["Account Status:", "Open / Current", "Last Reported:", "January 2026"],
    ]
    acct5_table = Table(acct5, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
    acct5_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8),
        ("FONT", (1, 0), (1, -1), "Helvetica", 8),
        ("FONT", (3, 0), (3, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    elements.append(acct5_table)
    elements.append(Spacer(1, 10))

    # Account 6 - Closed
    elements.append(Paragraph("WELLS FARGO ACTIVE CASH (CLOSED)", styles["SubHeader"]))
    acct6 = [
        ["Account Number:", "XXXX-XXXX-XXXX-3388", "Account Type:", "Revolving Credit Card"],
        ["Date Opened:", "February 2021", "Credit Limit:", "$6,000"],
        ["Current Balance:", "$0", "Monthly Payment:", "$0"],
        ["Payment Status:", "Paid / Closed", "Date Closed:", "September 2024"],
        ["Account Status:", "Closed by Consumer", "Last Reported:", "October 2024"],
    ]
    acct6_table = Table(acct6, colWidths=[1.4 * inch, 2.1 * inch, 1.4 * inch, 2.1 * inch])
    acct6_table.setStyle(TableStyle([
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 8),
        ("FONT", (1, 0), (1, -1), "Helvetica", 8),
        ("FONT", (3, 0), (3, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
    ]))
    elements.append(acct6_table)

    # ===== CREDIT INQUIRIES =====
    elements.append(Paragraph("CREDIT INQUIRIES", styles["SectionHeader"]))
    elements.append(Paragraph("Hard Inquiries (Last 24 Months): 5", styles["FieldValue"]))
    elements.append(Spacer(1, 6))

    inquiry_header = ["Date", "Creditor", "Type"]
    inquiry_data = [
        inquiry_header,
        ["12/10/2025", "CITI BANK, N.A.", "Credit Card"],
        ["09/22/2025", "CAPITAL ONE BANK", "Credit Card"],
        ["06/15/2025", "CHASE BANK USA", "Credit Card"],
        ["03/01/2025", "DISCOVER FINANCIAL", "Credit Card"],
        ["11/18/2024", "SYNCHRONY BANK", "Retail Card"],
    ]
    inquiry_table = Table(inquiry_data, colWidths=[1.5 * inch, 3.5 * inch, 2 * inch])
    inquiry_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
    ]))
    elements.append(inquiry_table)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Soft Inquiries: 3 (promotional / account review \u2014 do not affect score)", styles["SmallText"]))

    # ===== PUBLIC RECORDS =====
    elements.append(Paragraph("PUBLIC RECORDS", styles["SectionHeader"]))
    elements.append(Paragraph("No public records found.", styles["FieldValue"]))

    # ===== COLLECTIONS =====
    elements.append(Paragraph("COLLECTIONS", styles["SectionHeader"]))
    elements.append(Paragraph("No collection accounts found.", styles["FieldValue"]))

    # ===== SUMMARY =====
    elements.append(Paragraph("ACCOUNT SUMMARY", styles["SectionHeader"]))

    summary_header = ["Metric", "Value"]
    summary_data = [
        summary_header,
        ["Total Open Accounts", "5"],
        ["Total Closed Accounts", "1"],
        ["Total Balances", "$13,650"],
        ["Total Credit Limits", "$23,000"],
        ["Overall Utilization", "59.3%"],
        ["Revolving Utilization", "59.3%"],
        ["Oldest Account", "February 2021 (4 years, 11 months)"],
        ["Newest Account", "June 2024 (1 year, 7 months)"],
        ["Average Account Age", "2 years, 4 months"],
        ["On-Time Payments", "98.6% (71 of 72 months)"],
        ["Late Payments (30 days)", "1"],
        ["Late Payments (60+ days)", "0"],
        ["Hard Inquiries (24 months)", "5"],
    ]
    summary_table = Table(summary_data, colWidths=[3.5 * inch, 3.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 8),
        ("FONT", (1, 1), (1, -1), "Helvetica", 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
    ]))
    elements.append(summary_table)

    # ===== DISCLAIMER =====
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc"), spaceAfter=8))
    elements.append(Paragraph(
        "DISCLAIMER: This is a SYNTHETIC credit report generated for testing and development purposes only. "
        "All personal information, account details, and financial data contained herein are entirely fictional. "
        "This document does not represent any real individual's credit history. "
        "Do not use this document for any financial, legal, or official purpose.",
        styles["SmallText"]
    ))

    doc.build(elements)
    print(f"Sample credit report generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_report()
