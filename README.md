<h1 align="center">Data Extraction & Automation Tools</h1>

<p align="center">
  <b>Python scripts developed to automate data extraction and structuring for engineering and material tracking workflows.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/OCR-Tesseract-success?logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Data-pandas-orange?logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/PDF-PyMuPDF-lightgrey?logo=adobeacrobatreader&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-In%20Development-7130B1" />
</p>

---

## 🇺🇸 English Version

### 🧩 Overview
This repository contains a set of **Python automation scripts** designed to support internal workflows in large-scale **Transmission Line engineering projects**.  
They handle the extraction, cleaning, and structuring of unformatted data (from PDFs, images, and NFs) into usable Excel datasets.

> ⚠️ **Note:** This project is currently in **active development and testing phase**. Some modules are being optimized for broader use and improved robustness.

### ⚙️ Components
**1. `nf_extractor.py`**  
Performs end-to-end extraction of structured data from Brazilian invoices (NFs):  
- Uses **PDF text extraction** and **OCR (Tesseract)** as fallback.  
- Detects key information such as supplier name, invoice number, quantity, and unit value.  
- Writes the processed data directly into an Excel control sheet (`openpyxl`), filling missing cells in yellow.  
- Includes error handling, logging, and multiple regex strategies for robustness.

**2. `extracao_nf_alubar.py`**  
- Scans folders of PDF invoices.  
- Uses OCR to detect invoice numbers (`NF:` pattern) in the right section of each page.  
- Outputs a summary report (`resultado_NFs.txt`) listing all unique and repeated invoices found.  

**3. `planta_perfil.py`**  
- Extracts coordinate data from engineering layout PDFs.  
- Captures **tower identifiers**, **X/Y coordinates**, **elevation**, and **line angle** values via regex.  
- Exports a structured report (`resultado.txt`) for validation and integration into construction diagrams.

### 📊 Results
- Automated what used to be **hours of manual NF verification**.  
- Created **standardized outputs** ready for Excel dashboards.  
- Improved **traceability and auditability** of field and supplier data.

---

## 🇧🇷 Versão em Português

### 🧩 Visão Geral
Este repositório reúne **scripts de automação em Python** desenvolvidos para apoiar fluxos de trabalho internos em projetos de **Linhas de Transmissão**.  
Eles extraem, tratam e estruturam dados não formatados (de PDFs, imagens e NFs) para planilhas Excel e relatórios de acompanhamento.

> ⚠️ **Aviso:** Este projeto está em **fase ativa de desenvolvimento e testes**. Alguns módulos ainda estão sendo otimizados para uso mais amplo e maior robustez.

### ⚙️ Componentes
**1. `nf_extractor.py`**  
Realiza a extração completa de dados de **notas fiscais (NFs)** brasileiras:  
- Usa **leitura direta de PDF** e **OCR (Tesseract)** quando necessário.  
- Identifica **fornecedor, número da NF, quantidade e valor unitário**.  
- Grava os dados automaticamente em planilhas de controle Excel (`openpyxl`), destacando campos vazios em amarelo.  
- Contém logs e múltiplos padrões regex para lidar com formatos diferentes de NF.

**2. `extracao_nf_alubar.py`**  
- Varre pastas com PDFs e identifica **números de NF** por OCR.  
- Gera um relatório (`resultado_NFs.txt`) listando **todas as NFs únicas e repetidas**.  

**3. `planta_perfil.py`**  
- Extrai dados de coordenadas de **plantas e perfis de torres** em PDF.  
- Captura **número da torre, coordenadas X/Y, elevação e ângulo da linha**.  
- Exporta tudo em um relatório (`resultado.txt`) pronto para validação e integração em diagramas.

### 📊 Resultados
- Reduziu **horas de conferência manual** para minutos.  
- Padronizou a **estrutura de dados** para relatórios técnicos.  
- Aumentou a **precisão e rastreabilidade** dos dados de campo e fornecedores.

---

## 👨‍💻 Author / Autor
**Wesley Ryan Lopes da Rocha**  
[LinkedIn](https://www.linkedin.com/in/wryan-lopes/) | [Portfolio](https://ryan-wes.github.io/portfolio/)
