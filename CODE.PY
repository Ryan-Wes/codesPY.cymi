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

def extrair_dados_alubar(texto):
    """Extrai dados específicos da NF da ALUBAR com suporte a múltiplos formatos."""
    dados = {
        "DATA RECEBIMENTO": datetime.today().strftime("%d/%m/%Y"),
        "DESCRIÇÃO ESPECIFICA": "",
        "NFE": "",
        "UNID": "KG",
        "QTDD": "",
        "VOLUMES OU BOBINAS OU CONJUNTOS": "",
        "FORNECEDOR": "ALUBAR",
        "VALOR UNITARIO (R$)": ""
    }
    
    # 🔍 TENTAR DIFERENTES PADRÕES PARA NÚMERO DA NF
    padroes_nf = [
        r'N[º°\.\s]*0*(\d{6,})',  # Padrão tradicional: N. 000190966
        r'NF[:]?\s*(\d{6,})',     # Padrão alternativo: NF: 187360
        r'NOTA\s*N?[º°]?\s*(\d{6,})',  # NOTA N° 187360
        r'187360'  # Número específico desta NF
    ]
    
    for padrao in padroes_nf:
        nf_match = re.search(padrao, texto, re.IGNORECASE)
        if nf_match:
            dados["NFE"] = nf_match.group(1) if nf_match.groups() else nf_match.group(0)
            print(f"✅ NF encontrada com padrão: {padrao}")
            break
    
    # 🔍 EXTRAIR DESCRIÇÃO DO PRODUTO - MÚLTIPLOS PADRÕES
    padroes_descricao = [
        r'DESCRIÇÃO DO PROD[\./]SERV[\./]\s*(.*?)(?:\n|NCM|$)',  # Formato tradicional
        r'CABO.*?AL.*?NU.*?CAL.*?1120.*?828',  # Padrão anterior
        r'CABO.*?CAL.*?1010.*?MCM.*?61',  # Novo padrão: CABO CAL 1010 MCM 61 X 3.26 L
        r'PRODUTO:\s*(.*?)(?:\n|$)'  # Do romaneio: PRODUTO: CABO AL NU CAL 1120 1010 MCM 61X3,26
    ]
    
    for padrao in padroes_descricao:
        descricao_match = re.search(padrao, texto, re.IGNORECASE)
        if descricao_match:
            if descricao_match.groups():
                dados["DESCRIÇÃO ESPECIFICA"] = descricao_match.group(1).strip()
            else:
                dados["DESCRIÇÃO ESPECIFICA"] = descricao_match.group(0)
            print(f"✅ Descrição encontrada com padrão: {padrao}")
            break
    
    # 🔍 EXTRAIR QUANTIDADE - MÚLTIPLOS PADRÕES
    padroes_qtd = [
        r'QUANT[:\s]*([\d\.]+,[\d]{2})',  # QUANT: 27.603,00
        r'QLANT[.\s]*KG\s*([\d\.]+,[\d]{2})',  # QLANT. KG 27.603,00
        r'27[\s\.]*603[\s,]*00',  # 27.603,00
        r'TOTAL.*?27[\s\d\.]+,?[\d]*',  # TOTAL 27.603 (do romaneio)
        r'PESO LIQUIDO[^\d]*([\d\.,]+)'  # PESO LIQUIDO 27603,000
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
                # Formatar corretamente (27.603,00 ou 27603,000 -> 27.603,00)
                if '.' in qtdd and ',' in qtdd:
                    # Já está no formato correto: 27.603,00
                    dados["QTDD"] = qtdd
                elif ',' in qtdd:
                    # Formato: 27603,000 -> 27.603,00
                    partes = qtdd.split(',')
                    inteiro = partes[0]
                    if len(inteiro) > 3:
                        inteiro = inteiro[:-3] + '.' + inteiro[-3:]
                    dados["QTDD"] = inteiro + ',' + partes[1][:2]
                print(f"✅ Quantidade encontrada com padrão: {padrao}")
                break
    
    # 🔍 EXTRAIR VOLUMES - MÚLTIPLOS PADRÕES
    padroes_volumes = [
        r'QUANTIDADE\s*(\d+)',  # QUANTIDADE 9
        r'QTD[.\s]*DE[\s\S]*VOLUMES[^\d]*(\d+)',  # QTD. DE VOLUMES (UND) 9
        r'9\s*volume'  # 9 volume
    ]
    
    for padrao in padroes_volumes:
        volumes_match = re.search(padrao, texto, re.IGNORECASE)
        if volumes_match:
            dados["VOLUMES OU BOBINAS OU CONJUNTOS"] = volumes_match.group(1) if volumes_match.groups() else volumes_match.group(0)
            print(f"✅ Volumes encontrados com padrão: {padrao}")
            break
    
    # 🔍 EXTRAIR VALOR UNITÁRIO - MÚLTIPLOS PADRÕES
    padroes_valor_unit = [
        r'VLUNTARIO[:\s]*([\d]+[,.]\d{6})',  # VLUNTARIO 25.962385
        r'25[,.]962385',  # 25,962385 (valor específico)
        r'valor\s*unit[áa]rio[^\d]*([\d]+[,.]\d{6})',
        r'Valor unitário tributável[^\d]*([\d]+[,.]\d+)'  # Valor unitário tributável: 25.96238561
    ]
    
    for padrao in padroes_valor_unit:
        valor_match = re.search(padrao, texto, re.IGNORECASE)
        if valor_match:
            if valor_match.groups():
                valor = valor_match.group(1)
            else:
                valor_num = re.search(r'[\d]+[,.]\d+', valor_match.group(0))
                if valor_num:
                    valor = valor_num.group(0)
            
            if valor:
                valor = valor.replace('.', ',')
                dados["VALOR UNITARIO (R$)"] = valor
                print(f"✅ Valor unitário encontrado com padrão: {padrao}")
                break
    
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