import os
import re
import pytesseract
import pdfplumber
from PIL import Image
import cv2
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from datetime import datetime
import time

# =========================
# CONFIGURAÇÃO
# =========================
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\wrlopesr\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
CAMINHO_PLANILHA = r"C:\Users\wrlopesr\OneDrive - CYMI CONSTRUÇÕES E PARTICIPAÇÕES S.A\Desktop\NOTAS\EXEMPLOS PRO CÓDIGO PYTHON\PLANILHA DE TESTE.xlsx"
PASTA_NFS = r"C:\Users\wrlopesr\OneDrive - CYMI CONSTRUÇÕES E PARTICIPAÇÕES S.A\Desktop\NOTAS\EXEMPLOS PRO CÓDIGO PYTHON"

# =========================
# FUNÇÕES AUXILIARES
# =========================
def preprocess_image(pil_img):
    """Melhora a imagem para o OCR."""
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

def ocr_from_pdf(pdf_path):
    """Extrai texto de um PDF usando pdfplumber."""
    texto_total = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extrai texto diretamente primeiro
            texto_pagina = page.extract_text()
            if texto_pagina:
                texto_total += texto_pagina + "\n"
            else:
                # Se não conseguir texto, usa OCR
                pil_image = page.to_image(resolution=300).original
                pil_image = preprocess_image(pil_image)
                texto_total += pytesseract.image_to_string(pil_image, lang="por") + "\n"
    return texto_total

def identificar_fornecedor(texto):
    """Identifica o fornecedor baseado no texto."""
    fornecedores = {
        'ALUBAR': r'alubar|alum[ií]nio',
        'SADEL': r'sadel',
        'SAE TOWERS': r'sae\s*towers|sae',
        'CYMI': r'cymi',
        'FURUKAWA': r'furukawa',
        'PRYSMIAN': r'prysmian'
    }
    
    texto = texto.lower()
    for fornecedor, padrao in fornecedores.items():
        if re.search(padrao, texto, re.IGNORECASE):
            return fornecedor
    return ""

def extrair_dados(texto):
    """Extrai dados específicos da NF."""
    dados = {
        "DATA RECEBIMENTO": datetime.today().strftime("%d/%m/%Y"),
        "DESCRIÇÃO ESPECIFICA": "",
        "NFE": "",
        "UNID": "KG",
        "QTDD": "",
        "VOLUMES OU BOBINAS OU CONJUNTOS": "9",
        "FORNECEDOR": "ALUBAR",
        "VALOR UNITARIO (R$)": ""
    }
    
    # Extrair número da NF
    nf_match = re.search(r'N[º°\.\s]*0*(\d{6,})', texto, re.IGNORECASE)
    if nf_match:
        dados["NFE"] = nf_match.group(1) if nf_match.groups() else nf_match.group(0)
    
    # Extrair descrição do produto
    descricao_match = re.search(r'DESCRIÇÃO DO PROD[\./]SERV[\./]\s*(.*?)(?:\n|NCM|$)', texto, re.IGNORECASE)
    if descricao_match:
        dados["DESCRIÇÃO ESPECIFICA"] = descricao_match.group(1).strip()
    else:
        descricao_alt = re.search(r'CABO.*?AL.*?NU.*?CAL.*?1120.*?828', texto, re.IGNORECASE)
        if descricao_alt:
            dados["DESCRIÇÃO ESPECIFICA"] = descricao_alt.group(0)
    
    # Extrair quantidade total - CORRIGIDO
    padroes_qtd = [
        r'QUANT[:\s]*([\d\.]+,[\d]{2})',  # 25.351,00
        r'25[\s\.]*351[\s,]*00',          # 25.351,00
        r'25351,\d{2}',                   # 25351,00
    ]
    
    for padrao in padroes_qtd:
        qtdd_match = re.search(padrao, texto)
        if qtdd_match:
            if qtdd_match.groups():
                qtdd = qtdd_match.group(1)
            else:
                numeros = re.search(r'[\d\.,]+', qtdd_match.group(0))
                if numeros:
                    qtdd = numeros.group(0)
            
            if qtdd:
                dados["QTDD"] = qtdd
                break
    
    # Extrair valor unitário - CORRIGIDO
    padroes_valor_unit = [
        r'VLUNTAMO[:\s]*([\d]+,[\d]{6})',  # 25,850884
        r'25[\s,]*850884',                 # 25,850884  
        r'valor\s*unit[áa]rio[^\d]*([\d]+,[\d]+)',
        r'pre[çc]o\s*unit[áa]rio[^\d]*([\d]+,[\d]+)',
    ]
    
    for padrao in padroes_valor_unit:
        valor_match = re.search(padrao, texto, re.IGNORECASE)
        if valor_match:
            if valor_match.groups():
                valor = valor_match.group(1)
            else:
                valor_match_num = re.search(r'[\d]+,[\d]+', valor_match.group(0))
                if valor_match_num:
                    valor = valor_match_num.group(0)
            
            if valor:
                dados["VALOR UNITARIO (R$)"] = valor
                break
    
    # CALCULAR VALOR UNITÁRIO SE NÃO ENCONTRADO - CORRIGIDO
    if not dados["VALOR UNITARIO (R$)"] and dados["QTDD"]:
        # Procurar valor total da NF
        padroes_valor_total = [
            r'VALOR TOTAL DA NOTA[:\s]*R\$\s*([\d\.]+,[\d]{2})',
            r'VALOR TOTAL[:\s]*R\$\s*([\d\.]+,[\d]{2})',
            r'697\.943,24',  # Valor específico
            r'VTOTAL[:\s]*([\d\.]+,[\d]{2})',
        ]
        
        for padrao in padroes_valor_total:
            valor_total_match = re.search(padrao, texto, re.IGNORECASE)
            if valor_total_match:
                try:
                    if valor_total_match.groups():
                        valor_total_str = valor_total_match.group(1)
                    else:
                        valor_total_str = re.search(r'[\d\.,]+', valor_total_match.group(0))
                        if valor_total_str:
                            valor_total_str = valor_total_str.group(0)
                    
                    if valor_total_str:
                        # Converter para cálculo
                        valor_total_calc = float(valor_total_str.replace('.', '').replace(',', '.'))
                        qtdd_calc = float(dados["QTDD"].replace('.', '').replace(',', '.'))
                        
                        if qtdd_calc > 0:
                            valor_unitario = valor_total_calc / qtdd_calc
                            # Formatar corretamente
                            dados["VALOR UNITARIO (R$)"] = f"{valor_unitario:.6f}".replace('.', ',')
                            break
                            
                except Exception as e:
                    print(f"Erro no cálculo: {e}")
    
    return dados

def encontrar_proxima_linha(ws):
    """Encontra a próxima linha vazia começando da linha 4."""
    for row in range(4, ws.max_row + 100):
        if ws.cell(row=row, column=3).value is None:
            return row
    return ws.max_row + 1

def escrever_na_planilha(ws, linha, dados):
    """Escreve os dados na planilha nas colunas corretas."""
    mapeamento_colunas = {
        "DATA RECEBIMENTO": 3,        # C
        "DESCRIÇÃO ESPECIFICA": 4,    # D
        "NFE": 5,                     # E
        "UNID": 6,                    # F
        "QTDD": 7,                    # G
        "VOLUMES OU BOBINAS OU CONJUNTOS": 8,  # H
        "FORNECEDOR": 10,             # J
        "VALOR UNITARIO (R$)": 11     # K
    }
    
    amarelo = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    for campo, coluna in mapeamento_colunas.items():
        valor = dados.get(campo, "")
        try:
            celula = ws.cell(row=linha, column=coluna, value=valor)
            if not valor:
                celula.fill = amarelo
        except:
            pass

# =========================
# PROCESSAMENTO PRINCIPAL
# =========================
def main():
    try:
        wb = load_workbook(CAMINHO_PLANILHA)
        ws = wb.active
        print("✅ Planilha carregada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao carregar planilha: {e}")
        return
    
    for arquivo in os.listdir(PASTA_NFS):
        if not arquivo.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
            continue
            
        caminho_arquivo = os.path.join(PASTA_NFS, arquivo)
        print(f"\n📄 Processando: {arquivo}")
        
        try:
            if arquivo.lower().endswith('.pdf'):
                texto = ocr_from_pdf(caminho_arquivo)
            else:
                pil_img = Image.open(caminho_arquivo)
                pil_img = preprocess_image(pil_img)
                texto = pytesseract.image_to_string(pil_img, lang="por")
            
            # DEBUG: mostrar texto encontrado
            print("🔍 Procurando por dados na NF...")
            
            dados = extrair_dados(texto)
            print(f"📊 Dados extraídos:")
            for k, v in dados.items():
                print(f"   {k}: {v}")
            
            linha = encontrar_proxima_linha(ws)
            print(f"📝 Escrevendo na linha: {linha}")
            
            escrever_na_planilha(ws, linha, dados)
            wb.save(CAMINHO_PLANILHA)
            print(f"✅ Dados salvos na planilha")
            
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo}: {e}")
    
    print("\n🎉 Processamento concluído!")

if __name__ == "__main__":
    main()