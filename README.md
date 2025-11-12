# 🧠 NF Data Extractor | Python + OCR

Automation script developed to **extract and validate data from Brazilian invoices (NFs)** received from suppliers, optimizing manual verification in material management processes.

---

## 🇬🇧 English Version

### ⚙️ How it works
- Reads **PDF or image files** of invoices using **OCR (Optical Character Recognition)**.  
- Cleans and validates extracted text to identify **supplier names, invoice numbers, item codes, and quantities**.  
- Outputs structured data directly into **Excel spreadsheets** used for material tracking and control.  
- Reduces manual verification time from hours to just a few minutes.

### 🧩 Stack
- **Python 3**  
- **pytesseract** (OCR engine)  
- **pandas** for data structuring and export  
- **openpyxl** for Excel integration  
- **re** and **string processing** for cleaning NF data  

### 📊 Use case
Originally built to support operations at an international **Transmission Line company**, improving accuracy and efficiency in invoice validation.

### 🚀 Results
- Reduced human error in NF transcription by **~90%**.  
- Processing time per batch dropped from ~2 hours to **under 10 minutes**.  
- Data automatically formatted for internal Excel dashboards.

---

## 🇧🇷 Versão em Português

### ⚙️ Como funciona
- Lê **arquivos PDF ou imagens** de notas fiscais (NFs) utilizando **OCR (Reconhecimento Óptico de Caracteres)**.  
- Limpa e valida os textos extraídos para identificar **fornecedores, números de NF, códigos de item e quantidades**.  
- Exporta os dados estruturados diretamente para **planilhas do Excel**, usadas no controle e rastreamento de materiais.  
- Reduz o tempo de conferência manual de horas para apenas alguns minutos.

### 🧩 Tecnologias utilizadas
- **Python 3**  
- **pytesseract** (motor OCR)  
- **pandas** para estruturação e exportação de dados  
- **openpyxl** para integração com Excel  
- **re** e manipulação de strings para limpeza dos dados  

### 📊 Caso de uso
Projeto criado para otimizar processos em uma **empresa internacional de Linha de Transmissão**, aumentando a precisão e eficiência na validação de notas fiscais.

### 🚀 Resultados
- Redução de cerca de **90% nos erros manuais** de digitação.  
- Tempo médio de processamento caiu de ~2h para **menos de 10 minutos**.  
- Dados gerados automaticamente no formato exigido pelos relatórios internos do Excel.

---

## 📁 Files / Arquivos
- `EXTRAÇÃO DE NFs ALUBAR POMPEU.py` → main OCR and extraction script / script principal de OCR e extração  
- `PLANTAePERFIL.py` → helper for data transformation / script auxiliar para formatação dos dados  
- `CODE.PY` / `CODES.PY` → older testing scripts / versões anteriores para testes  

---

## 👨‍💻 Author / Autor
**Wesley Ryan Lopes da Rocha**  
[LinkedIn](https://www.linkedin.com/in/wryan-lopes/) | [Portfolio](https://ryan-wes.github.io/portfolio/)
