import os
from fpdf import FPDF
from datetime import datetime

class ReportPDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('helvetica', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, 'Tu Checklist Vehicular - AutoTramite MX', border=0, align='C')
        # Line break
        self.ln(20)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('helvetica', 'I', 8)
        # Page number
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')

def generate_pdf_checklist(titulo_tramite: str, requisitos_lista: list[str]) -> str:
    """
    Genera un archivo PDF con un checklist listo para imprimir.
    Retorna la ruta del archivo generado.
    """
    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    # Subtitulo
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f'Trámite: {titulo_tramite}', ln=True)
    pdf.cell(0, 10, f'Fecha de consulta: {datetime.now().strftime("%d/%m/%Y")}', ln=True)
    pdf.ln(10)
    
    # Lista de requisitos
    pdf.set_font('helvetica', size=12)
    pdf.cell(0, 10, 'Requisitos a presentar (marca la casilla al reunirlos):', ln=True)
    pdf.ln(5)
    
    for req in requisitos_lista:
        # Codificamos a latin-1 para compatibilidad básica en FPDF si usamos fuentes estandar
        # Pero fpdf2 maneja unicode por defecto con fuentes integradas. Usamos fpdf2.
        req_clean = req.replace("✅", "").replace("✔️", "").strip()
        pdf.cell(10, 10, "[   ]", border=0)
        pdf.multi_cell(0, 10, txt=req_clean)
        pdf.ln(2)
        
    os.makedirs("output", exist_ok=True)
    filename = f"output/checklist_{int(datetime.now().timestamp())}.pdf"
    pdf.output(filename)
    
    return filename
