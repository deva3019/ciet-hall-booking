from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from datetime import datetime

# Create PDF
pdf_filename = "CIET_Hall_Booking_System_Report.pdf"
doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
story = []
styles = getSampleStyleSheet()

# Title Style
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#4f46e5'),
    spaceAfter=6,
    alignment=1
)

# Heading Style
heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=colors.HexColor('#1e293b'),
    spaceAfter=12,
    spaceBefore=12
)

# Add Title
story.append(Paragraph("CIET HALL BOOKING MANAGEMENT SYSTEM", title_style))
story.append(Paragraph("Project Report", styles['Normal']))
story.append(Spacer(1, 0.3*inch))

# Add Date
story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
story.append(Spacer(1, 0.2*inch))

# Project Overview
story.append(Paragraph("PROJECT OVERVIEW", heading_style))
overview_text = """
A <b>web-based smart hall booking system</b> for CIET that streamlines the process of booking auditoriums and seminar halls online. The system automates the entire booking workflow from request submission to approval and provides real-time availability tracking.
"""
story.append(Paragraph(overview_text, styles['Normal']))
story.append(Spacer(1, 0.2*inch))

# Live Link
story.append(Paragraph("<b>Live Link:</b> https://ciet-hall-booking.onrender.com", styles['Normal']))
story.append(Spacer(1, 0.3*inch))

# Key Features
story.append(Paragraph("KEY FEATURES", heading_style))
features = [
    "✓ User Roles & Authentication (Staff, HOD, Principal)",
    "✓ 3 Halls with Real-time Availability Calendar (60-day view)",
    "✓ Flexible Time Slots (Forenoon, Afternoon, Full Day)",
    "✓ Export to Calendar (.ics format) & PDF Reports",
    "✓ Email Notifications for Approvals",
    "✓ IST Timezone Support",
    "✓ Dark/Light Mode Support",
    "✓ Mobile Responsive Design",
    "✓ Dashboard Analytics with Filters"
]
for feature in features:
    story.append(Paragraph(feature, styles['Normal']))
story.append(Spacer(1, 0.2*inch))

# Technology Stack
story.append(Paragraph("TECHNOLOGY STACK", heading_style))
tech_data = [
    ['Component', 'Technology'],
    ['Frontend', 'HTML5, Tailwind CSS, JavaScript'],
    ['Backend', 'Python Flask'],
    ['Database', 'MongoDB'],
    ['Hosting', 'Render (Cloud)'],
    ['Version Control', 'GitHub']
]
tech_table = Table(tech_data, colWidths=[2*inch, 3*inch])
tech_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))
story.append(tech_table)
story.append(Spacer(1, 0.2*inch))

# Main Modules
story.append(Paragraph("MAIN MODULES", heading_style))
modules = [
    "<b>Authentication:</b> Login/Signup with secure JWT tokens",
    "<b>Booking:</b> Create and manage booking requests",
    "<b>Availability:</b> Real-time hall availability calendar",
    "<b>Approval:</b> HOD review and approval workflow",
    "<b>Reports:</b> PDF and ICS export functionality",
    "<b>Dashboard:</b> Track personal bookings and statistics"
]
for module in modules:
    story.append(Paragraph(module, styles['Normal']))
story.append(Spacer(1, 0.2*inch))

# Completed Deliverables
story.append(Paragraph("COMPLETED DELIVERABLES", heading_style))
deliverables = [
    "✓ User authentication system",
    "✓ Hall booking with availability calendar",
    "✓ Approval workflow with HOD review",
    "✓ PDF report generation",
    "✓ ICS calendar export",
    "✓ Mobile responsive design",
    "✓ IST timezone implementation",
    "✓ Dark/Light mode support",
    "✓ Production deployment",
    "✓ Complete GitHub repository"
]
for deliverable in deliverables:
    story.append(Paragraph(deliverable, styles['Normal']))
story.append(Spacer(1, 0.3*inch))

# Benefits
story.append(Paragraph("BENEFITS", heading_style))
benefits = [
    "✓ Saves Time - No manual paper-based booking",
    "✓ Transparent - Complete visibility of bookings",
    "✓ Efficient - Automated approval workflow",
    "✓ Accessible - 24/7 online availability",
    "✓ Mobile Friendly - Works on all devices",
    "✓ Data Secure - Encrypted authentication"
]
for benefit in benefits:
    story.append(Paragraph(benefit, styles['Normal']))
story.append(Spacer(1, 0.3*inch))

# Testing Status
story.append(Paragraph("TESTING STATUS", heading_style))
test_data = [
    ['Test Type', 'Status'],
    ['Desktop Testing', '✓ Passed'],
    ['Mobile Testing', '✓ Passed'],
    ['API Testing', '✓ Passed'],
    ['Database Operations', '✓ Passed'],
    ['User Authentication', '✓ Passed'],
    ['Booking Workflow', '✓ Passed']
]
test_table = Table(test_data, colWidths=[2.5*inch, 2.5*inch])
test_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))
story.append(test_table)
story.append(Spacer(1, 0.3*inch))

# Footer
story.append(Paragraph("_" * 80, styles['Normal']))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("<b>Developer:</b> Deva Veera Kumaran | <b>Year:</b> 3rd Year CS | <b>Date:</b> November 1, 2025", styles['Normal']))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("<b>Tagline:</b> Smart Booking, Better Management ✨", styles['Normal']))

# Build PDF
doc.build(story)
print(f"✅ PDF created: {pdf_filename}")
