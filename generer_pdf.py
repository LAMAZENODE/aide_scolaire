# generer_pdf.py
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

def generer_pdf(texte_correction, enonce_exercice, matiere="maths"):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=40, 
        leftMargin=40, 
        topMargin=40, 
        bottomMargin=40,
        title="Correction Tuteur Scolaire IA"
    )
    
    styles = getSampleStyleSheet()
    
    style_titre = ParagraphStyle(
        'TitrePDF', parent=styles['Heading1'], 
        fontSize=22, leading=26, textColor='#1E3A8A', alignment=TA_CENTER, spaceAfter=20
    )
    
    style_sous_titre = ParagraphStyle(
        'SousTitrePDF', parent=styles['Heading2'], 
        fontSize=14, leading=18, textColor='#10B981', spaceBefore=15, spaceAfter=10
    )
    
    style_corps = ParagraphStyle(
        'CorpsPDF', parent=styles['BodyText'], 
        fontSize=11, leading=16, textColor='#374151', alignment=TA_JUSTIFY, spaceAfter=10
    )
    
    style_enonce = ParagraphStyle(
        'EnoncePDF', parent=styles['Italic'], 
        fontSize=10, leading=14, textColor='#6B7280', spaceAfter=15
    )
    
    style_footer = ParagraphStyle(
        'FooterPDF', parent=styles['Normal'], 
        fontSize=8, leading=10, textColor='#9CA3AF', alignment=TA_CENTER, spaceBefore=30
    )
    
    histoire = []
    histoire.append(Paragraph("📐 Tuteur Scolaire IA - Correction", style_titre))
    histoire.append(Spacer(1, 10))
    histoire.append(Paragraph(f"📚 Matière : {matiere.upper()}", style_sous_titre))
    histoire.append(Spacer(1, 5))
    
    # Énoncé
    histoire.append(Paragraph("✍️ Question posée :", style_sous_titre))
    enonce_propre = enonce_exercice.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    enonce_propre = enonce_propre.replace('\n', '<br/>')
    histoire.append(Paragraph(enonce_propre, style_enonce))
    histoire.append(Spacer(1, 10))
    
    # Nettoyage et conversion de la réponse de l'IA
    histoire.append(Paragraph("📝 Réponse détaillée :", style_sous_titre))
    
    # 1. Sécurité XML pour éviter les crashs sur < ou >
    texte_propre = texte_correction.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # 2. Remplacement des sauts de ligne
    texte_propre = texte_propre.replace('\n', '<br/>')
    
    # 3. Nettoyage des symboles LaTeX ($ et $$)
    texte_propre = texte_propre.replace('$$', '')
    texte_propre = texte_propre.replace('$', '')
    
    # 4. Conversion du Markdown en HTML ReportLab
    texte_propre = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texte_propre) # Gras
    texte_propre = re.sub(r'\*(.*?)\*', r'<i>\1</i>', texte_propre)     # Italique
    texte_propre = re.sub(r'### (.*?)<br/>', r'<b><font color="#1E3A8A">\1</font></b><br/>', texte_propre) # Titres de chapitres

    histoire.append(Paragraph(texte_propre, style_corps))

        # Remplacez cette ligne (vers la fin du fichier) :
    # histoire.append(Spacer(1, 20))
    
    # Par celle-ci :
    histoire.append(Spacer(1, 10))
    histoire.append(Paragraph("Document généré par Tuteur Scolaire IA - © 2026", style_footer))

    
    doc.build(histoire)
    buffer.seek(0)
    return buffer

