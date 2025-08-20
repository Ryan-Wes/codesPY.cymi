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
def verificar_arquivo_aberto(caminho_arquivo):
    """Verifica se o arquivo está aberto por outro processo."""
    try:
        with open(caminho_arquivo, 'a') as f:
            pass
        return False
    except PermissionError:
        return True

def esperar_arquivo_liberado(caminho_arquivo, max_tentativas=10):
    """Aguarda até que o arquivo seja liberado."""
    for tentativa in range(max_tentativas):
        if not verificar_arquivo_aberto(caminho_arquivo):
            return True
        print(f"Arquivo ocupado. Tentativa {tentativa + 1}/{max_tentativas}...")
        time.sleep(2)
    return False

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
            pil_image = page.to_image(resolution=300).original
            pil_image = preprocess_image(pil_image)
            texto_total += pytesseract.image_to_string(pil_image, lang="por") + "\n"
    return texto_total

def ocr_from_image(img_path):
    """Extrai texto de uma imagem."""
    pil_img = Image.open(img_path)
    pil_img = preprocess_image(pil_img)
    return pytesseract.image_to_string(pil_img, lang="por")

def identificar_fornecedor(texto):
    """Identifica o fornecedor baseado no texto."""
    fornecedores = {
        'ALUBAR': r'alubar|alum[ií]nio|alubar',
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
    """Aplica regex flexível para extrair os campos específicos."""
    texto_limpo = re.sub(r"\s+", " ", texto).strip()
    
    # Padrões de regex para extração
    padrao_nf = r"(?:NF|Nota Fiscal|NFe|Nº\s*)[^\d]{0,10}(\d{3,})"
    padrao_data = r"(\d{2}[-/]\d{2}[-/]\d{4})"
    padrao_valor_unitario = r"(?:valor\s*unit[áa]rio|pre[çc]o\s*unit[áa]rio)[^\d]*([R$]?\s*\d{1,3}(?:\.\d{3})*,\d{2})"
    padrao_valor_total = r"(?:valor\s*total|total\s*da\s*nota)[^\d]*([R$]?\s*\d{1,3}(?:\.\d{3})*,\d{2})"
    padrao_quantidade = r"(?:quantidade|qtd|qtde)[^\d]*(\d+(?:,\d+)?)"
    padrao_unidade = r"(?:unidade|unid\.?)[\s:]*([A-Za-z]{2,3})"
    padrao_descricao = r"(?:descri[çc][ãa]o|especifica[çc][ãa]o)[\s:]*([A-Za-z0-9\sÀ-ÿ\-]+?)(?=\n|$|quantidade|qtd|valor)"
    padrao_volumes = r"(?:volumes|bobinas|conjuntos)[\s:]*(\d+)"
    
    # Extração dos dados
    nf_numero = re.search(padrao_nf, texto_limpo, re.IGNORECASE)
    data_emissao = re.search(padrao_data, texto_limpo)
    valor_unitario = re.search(padrao_valor_unitario, texto_limpo, re.IGNORECASE)
    valor_total = re.search(padrao_valor_total, texto_limpo, re.IGNORECASE)
    quantidade = re.search(padrao_quantidade, texto_limpo, re.IGNORECASE)
    unidade = re.search(padrao_unidade, texto_limpo, re.IGNORECASE)
    descricao = re.search(padrao_descricao, texto_limpo, re.IGNORECASE)
    volumes = re.search(padrao_volumes, texto_limpo, re.IGNORECASE)
    
    fornecedor = identificar_fornecedor(texto_limpo)
    
    return {
        "DATA RECEBIMENTO": datetime.today().strftime("%d/%m/%Y"),
        "DESCRIÇÃO ESPECIFICA": descricao.group(1).strip() if descricao else "",
        "NFE": nf_numero.group(1) if nf_numero else "",
        "UNID": unidade.group(1).upper() if unidade else "",
        "QTDD": quantidade.group(1) if quantidade else "",
        "VOLUMES OU BOBINAS OU CONJUNTOS": volumes.group(1) if volumes else "",
        "FORNECEDOR": fornecedor,
        "VALOR UNITARIO (R$)": valor_unitario.group(1).replace("R$", "").strip() if valor_unitario else "",
    }

def encontrar_proxima_linha(ws):
    """Acha a primeira linha vazia na planilha, pulando células mescladas."""
    for row in range(2, ws.max_row + 2):
        # Verifica se a célula C (coluna 3) está vazia e não é mesclada
        celula_c = ws.cell(row=row, column=3)
        if hasattr(celula_c, 'value') and celula_c.value is None:
            return row
    return ws.max_row + 1

def is_celula_mesclada(ws, row, col):
    """Verifica se uma célula está em um range mesclado."""
    for merged_range in ws.merged_cells.ranges:
        if merged_range.min_row <= row <= merged_range.max_row and \
           merged_range.min_col <= col <= merged_range.max_col:
            return True
    return False

def escrever_em_celula(ws, row, col, valor, fill=None):
    """Escreve em uma célula, lidando com células mescladas."""
    try:
        celula = ws.cell(row=row, column=col)
        celula.value = valor
        if fill:
            celula.fill = fill
        return True
    except AttributeError as e:
        if "'MergedCell' object attribute 'value' is read-only" in str(e):
            print(f"Aviso: Célula {row},{col} está mesclada. Pulando...")
            return False
        else:
            raise

# =========================
# PROCESSAMENTO
# =========================
if not esperar_arquivo_liberado(CAMINHO_PLANILHA):
    print("❌ Não foi possível acessar a planilha. Verifique se ela está fechada.")
    exit()

try:
    wb = load_workbook(CAMINHO_PLANILHA)
    ws = wb.active
except Exception as e:
    print(f"❌ Erro ao carregar a planilha: {e}")
    exit()

amarelo = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

# Mapeamento direto das colunas que você quer preencher
colunas_alvo = {
    "DATA RECEBIMENTO": 3,        # Coluna C
    "DESCRIÇÃO ESPECIFICA": 4,    # Coluna D  
    "NFE": 5,                     # Coluna E
    "UNID": 6,                    # Coluna F
    "QTDD": 7,                    # Coluna G
    "VOLUMES OU BOBINAS OU CONJUNTOS": 8,  # Coluna H
    "FORNECEDOR": 10,             # Coluna J
    "VALOR UNITARIO (R$)": 11     # Coluna K
}

for arquivo in os.listdir(PASTA_NFS):
    caminho_arquivo = os.path.join(PASTA_NFS, arquivo)
    
    if not (arquivo.lower().endswith(".pdf") or arquivo.lower().endswith((".png", ".jpg", ".jpeg"))):
        continue
        
    if arquivo.lower().endswith(".pdf"):
        print(f"Processando PDF: {arquivo}")
        texto = ocr_from_pdf(caminho_arquivo)
    else:
        print(f"Processando Imagem: {arquivo}")
        texto = ocr_from_image(caminho_arquivo)

    print("\n=== TEXTO EXTRAÍDO DO OCR ===")
    print(texto[:500] + "..." if len(texto) > 500 else texto)
    print("=== FIM DO TEXTO ===\n")

    dados = extrair_dados(texto)
    linha = encontrar_proxima_linha(ws)
    
    print(f"Dados extraídos: {dados}")
    print(f"Linha para preencher: {linha}")
    
    # Preencher as colunas específicas
    for coluna_nome, col_idx in colunas_alvo.items():
        valor = dados.get(coluna_nome, "")
        
        print(f"Preenchendo coluna {col_idx} com: '{valor}'")
        
        # Verificar se a célula está mesclada
        if is_celula_mesclada(ws, linha, col_idx):
            print(f"Aviso: Célula {linha},{col_idx} está mesclada. Pulando...")
            continue
            
        sucesso = escrever_em_celula(ws, linha, col_idx, valor, amarelo if not valor else None)
        
        if not sucesso:
            print(f"Erro ao preencher célula {linha},{col_idx}")

    # Salvar após cada arquivo processado
    try:
        wb.save(CAMINHO_PLANILHA)
        print(f"✅ Dados da NF {dados.get('NFE', 'N/A')} adicionados na linha {linha}")
        print(f"✅ Planilha salva: {CAMINHO_PLANILHA}")
    except Exception as e:
        print(f"❌ Erro ao salvar planilha: {e}")

print("✅ Processamento concluído!")