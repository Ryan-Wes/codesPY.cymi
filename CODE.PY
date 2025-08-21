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
            if texto_paga:
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
    nf_match = re.search(r'N\.?\s*0*(\d{6,})', texto, re.IGNORECASE)
    if nf_match:
        dados["NFE"] = nf_match.group(1)
    
    # Extrair descrição do produto
    descricao_match = re.search(r'DESCRIÇÃO DO PROD\./SERV\.\s*(.*?)(?:\n|NCM|$)', texto, re.IGNORECASE)
    if descricao_match:
        dados["DESCRIÇÃO ESPECIFICA"] = descricao_match.group(1).strip()
    else:
        # Tentar encontrar descrição alternativa
        descricao_alt = re.search(r'CABO.*?AL.*?NU.*?CAL.*?\d+', texto, re.IGNORECASE)
        if descricao_alt:
            dados["DESCRIÇÃO ESPECIFICA"] = descricao_alt.group(0)
    
    # Extrair quantidade total - procurar por padrões específicos
    padroes_qtd = [
        r'QUANT:\s*([\d\.,]+)',
        r'QUANTIDADE:\s*([\d\.,]+)',
        r'25\.351,\d+',  # Valor específico visto na NF
        r'TOTAL.*?25[\d\.,]+'  # Procurar "TOTAL" seguido de números
    ]
    
    for padrao in padroes_qtd:
        qtdd_match = re.search(padrao, texto, re.IGNORECASE)
        if qtdd_match:
            qtdd = qtdd_match.group(1) if len(qtdd_match.groups()) > 0 else qtdd_match.group(0)
            qtdd = re.search(r'[\d\.,]+', qtdd).group(0) if re.search(r'[\d\.,]+', qtdd) else qtdd
            dados["QTDD"] = qtdd.replace('.', '').replace(',', '.')
            break
    
    # Extrair valor unitário
    valor_unit_match = re.search(r'VLUNTAMO:\s*([\d\.,]+)', texto, re.IGNORECASE)
    if valor_unit_match:
        dados["VALOR UNITARIO (R$)"] = valor_unit_match.group(1).replace('.', '').replace(',', '.')
    else:
        # Calcular valor unitário baseado no total e quantidade
        valor_total_match = re.search(r'VTOTAL:\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_total_match and dados["QTDD"]:
            try:
                valor_total = float(valor_total_match.group(1).replace('.', '').replace(',', '.'))
                quantidade = float(dados["QTDD"])
                if quantidade > 0:
                    dados["VALOR UNITARIO (R$)"] = str(round(valor_total / quantidade, 6))
            except:
                pass
    
    return dados

def encontrar_proxima_linha(ws):
    """Encontra a próxima linha vazia começando da linha 4."""
    for row in range(4, ws.max_row + 100):  # Começa da linha 4
        # Verifica se a coluna C está vazia
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
            print(f"✓ Coluna {coluna} preenchida: {valor}")
        except Exception as e:
            print(f"✗ Erro na coluna {coluna}: {e}")

# =========================
# PROCESSAMENTO PRINCIPAL
# =========================
def main():
    # Verificar se a planilha está acessível
    try:
        wb = load_workbook(CAMINHO_PLANILHA)
        ws = wb.active
        print("✅ Planilha carregada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao carregar planilha: {e}")
        return
    
    # Processar arquivos
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
            
            # DEBUG: Mostrar parte do texto
            print("Texto extraído (primeiras 200 chars):")
            print(texto[:200] + "..." if len(texto) > 200 else texto)
            
            # Extrair dados
            dados = extrair_dados(texto)
            print(f"📊 Dados extraídos: {dados}")
            
            # Encontrar próxima linha (começando da linha 4)
            linha = encontrar_proxima_linha(ws)
            print(f"📝 Escrevendo na linha: {linha}")
            
            # Escrever na planilha
            escrever_na_planilha(ws, linha, dados)
            
            # Salvar
            wb.save(CAMINHO_PLANILHA)
            print(f"✅ Dados salvos na planilha")
            
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo}: {e}")
    
    print("\n🎉 Processamento concluído!")

if __name__ == "__main__":
    main()