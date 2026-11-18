"""Gera o relatório da A2 em DOCX (layout de conferência do IEEE) e em LaTeX (IEEEtran).

As duas saídas são renderizadas a partir da mesma lista de blocos
(`relatorio_blocos.py`), de modo que não podem divergir. Depois da geração, o DOCX é
convertido em PDF pelo LibreOffice e o número de páginas é conferido.

Uso:  python Modelagem_A2/gerar_relatorio_A2.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preprocessamento as pp
import relatorio_blocos as rb

RAIZ = pp.raiz_projeto(Path(__file__).resolve().parent)
SAIDA_DOCX = RAIZ / 'relatorio_A2.docx'
SAIDA_TEX = RAIZ / 'relatorio_A2.tex'
SAIDA_PDF = RAIZ / 'relatorio_A2.pdf'
MAX_PAGINAS = 5

ROMANOS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
LARGURA_COLUNA = 3.4          # polegadas úteis dentro de uma coluna
LARGURA_TOTAL = 7.1           # polegadas úteis nas duas colunas

# Colunas mostradas em cada tabela e se ela ocupa a largura total da página.
# Todas as tabelas cabem numa coluna: uma tabela de largura total exigiria uma seção de
# coluna única no meio do texto, e o salto deixaria meia página em branco.
TABELAS = {
    'tabela_comparativa': {
        'largura_total': False, 'fonte': 6.6,
        'colunas': ['modelo', 'AUC validação cruzada (média ± dp)', 'AUC teste', 'IC 95% (teste)',
                    'sensibilidade', 'especificidade', 'F1'],
        'renomear': {'AUC validação cruzada (média ± dp)': 'AUC val. cruz.', 'AUC teste': 'AUC teste',
                     'IC 95% (teste)': 'IC 95%', 'sensibilidade': 'sens.',
                     'especificidade': 'espec.'},
        'larguras': [0.78, 0.62, 0.34, 0.60, 0.34, 0.34, 0.33],
    },
    'regua_vazamento': {
        'largura_total': False, 'fonte': 6.6,
        'colunas': ['cenário', 'atributos', 'modelo', 'AUC validação cruzada', 'AUC teste'],
        'renomear': {'atributos': 'atr.', 'AUC validação cruzada': 'AUC val. cruz.',
                     'AUC teste': 'AUC teste'},
        'larguras': [1.06, 0.26, 0.78, 0.66, 0.59],
    },
    'deriva_temporal': {
        'largura_total': False, 'fonte': 6.6,
        'colunas': ['protocolo', 'consultas de validação', '% Anormal na validação',
                    'Regressão Logística', 'Gradient Boosting'],
        'renomear': {'consultas de validação': 'valid. (n)', '% Anormal na validação': '% An.',
                     'Regressão Logística': 'logística', 'Gradient Boosting': 'boosting'},
        'larguras': [1.42, 0.42, 0.37, 0.58, 0.56],
    },
    'matriz_confusao': {
        'largura_total': False, 'fonte': 7.0,
        'larguras': [1.08, 1.16, 1.16],
    },
    'erros_por_faixa': {
        'largura_total': False, 'fonte': 6.6,
        'colunas': ['faixa etária', 'n', '% Anormal', 'sensibilidade', 'especificidade',
                    'Anormais não encontrados'],
        'renomear': {'faixa etária': 'faixa (anos)', '% Anormal': '% An.',
                     'sensibilidade': 'sens.', 'especificidade': 'espec.',
                     'Anormais não encontrados': 'An. perdidos'},
        'larguras': [0.70, 0.36, 0.40, 0.44, 0.48, 0.57],
    },
    'erros_por_motivo': {
        'largura_total': False, 'fonte': 6.6,
        'colunas': ['motivo principal', 'n', '% Anormal', 'sensibilidade', 'especificidade',
                    'Anormais não encontrados'],
        'renomear': {'% Anormal': '% An.', 'sensibilidade': 'sens.', 'especificidade': 'espec.',
                     'Anormais não encontrados': 'An. perdidos'},
        'larguras': [1.06, 0.30, 0.34, 0.38, 0.40, 0.47],
    },
}
# A matriz de confusão é quadrada e pequena: esticada até a largura da coluna, ficaria com
# letras maiores que as do texto.
LARGURA_FIGURA = {}
# Nas tabelas, os nomes dos modelos entram abreviados: por extenso, "Regressão Logística" sozinha
# consome um terço da largura de uma coluna do IEEE.
ABREVIAR_MODELO = {'Regressão Logística': 'Logística', 'Random Forest': 'Random forest',
                   'Gradient Boosting': 'Gradient boosting', 'Dummy': 'Classe majoritária'}


# --------------------------------------------------------------------- DOCX
def _borda(elemento, lados, tamanho=8):
    tcpr = elemento.get_or_add_tcPr() if elemento.tag.endswith('tc') else None
    alvo = tcpr if tcpr is not None else elemento
    borders = OxmlElement('w:tcBorders') if tcpr is not None else OxmlElement('w:tblBorders')
    for lado in ['top', 'left', 'bottom', 'right']:
        b = OxmlElement(f'w:{lado}')
        if lado in lados:
            b.set(qn('w:val'), 'single')
            b.set(qn('w:sz'), str(tamanho))
            b.set(qn('w:color'), '000000')
        else:
            b.set(qn('w:val'), 'none')
            b.set(qn('w:sz'), '0')
        borders.append(b)
    alvo.append(borders)


def _colunas(section, num, espaco_twips=360):
    sectPr = section._sectPr
    cols = sectPr.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols')
        sectPr.append(cols)
    cols.set(qn('w:num'), str(num))
    cols.set(qn('w:space'), str(espaco_twips))
    cols.set(qn('w:equalWidth'), '1')


def _pagina(section):
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin, section.bottom_margin = Inches(0.75), Inches(1.0)
    section.left_margin = section.right_margin = Inches(0.625)


def _par(doc, texto='', tamanho=10, negrito=False, italico=False, alinhamento=None,
         antes=0, depois=0, recuo=0.0, versalete=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(antes), Pt(depois)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.first_line_indent = Inches(recuo)
    p.alignment = alinhamento if alinhamento is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
    # Trechos entre asteriscos saem em itálico (termos estrangeiros e ênfase), como pede o IEEE.
    for trecho, enfase in _trechos(texto) if texto else []:
        r = p.add_run(trecho)
        r.font.size, r.font.bold = Pt(tamanho), negrito
        r.font.italic = italico or enfase
        r.font.small_caps = versalete
        r.font.name = 'Times New Roman'
    return p


def resolver_referencias(blocos):
    """Substitui {fig:nome} e {tab:nome} pelo número que a figura ou tabela recebe no documento.

    Assim o texto nunca cita um número errado quando uma figura é inserida ou retirada - o erro
    mais fácil de cometer e o mais difícil de notar numa revisão.
    """
    numeros = {}
    n_fig = n_tab = 0
    for b in blocos:
        if b[0] == 'fig':
            n_fig += 1
            numeros[f'fig:{b[1]}'] = str(n_fig)
        elif b[0] == 'tab':
            n_tab += 1
            numeros[f'tab:{b[1]}'] = ROMANOS[n_tab - 1]

    def trocar(texto):
        def um(m):
            if m.group(1) not in numeros:
                raise KeyError(f'referência a {m.group(1)}, que não existe no documento')
            return numeros[m.group(1)]
        return re.sub(r'\{((?:fig|tab):[\w]+)\}', um, texto)

    saida = []
    for b in blocos:
        pos = 2 if b[0] in ('fig', 'tab') else 1       # legenda da figura/tabela, ou o texto
        if len(b) > pos and isinstance(b[pos], str):
            b = b[:pos] + (trocar(b[pos]),) + b[pos + 1:]
        saida.append(b)
    return saida


def _trechos(texto):
    """Divide o texto em (trecho, é_itálico) a partir dos marcadores *...*."""
    return [(parte, i % 2 == 1) for i, parte in enumerate(re.split(r'\*(.+?)\*', texto)) if parte]


def gerar_docx(blocos, res, caminho):
    doc = Document()
    estilo = doc.styles['Normal']
    estilo.font.name = 'Times New Roman'
    estilo.font.size = Pt(10)
    estilo.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    pf = estilo.paragraph_format
    pf.space_before = pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE

    # --- seção 1: bloco do título, em coluna única (largura total da página)
    s1 = doc.sections[0]
    _pagina(s1)
    _colunas(s1, 1)
    _par(doc, rb.TITULO, tamanho=24, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, depois=8)
    _par(doc, ', '.join(rb.AUTORAS), tamanho=11, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, depois=1)
    _par(doc, rb.AFILIACAO, tamanho=10, italico=True,
         alinhamento=WD_ALIGN_PARAGRAPH.CENTER, depois=1)
    _par(doc, rb.DISCIPLINA, tamanho=10, italico=True,
         alinhamento=WD_ALIGN_PARAGRAPH.CENTER, depois=10)

    # --- seção 2: corpo em duas colunas
    s2 = doc.add_section(WD_SECTION.CONTINUOUS)
    _pagina(s2)
    _colunas(s2, 2)

    estado = {'h1': 0, 'h2': 0, 'fig': 0, 'tab': 0, 'colunas': 2}

    def voltar_para(n_colunas):
        """Tabelas largas exigem uma seção de coluna única; o texto volta para duas."""
        if estado['colunas'] == n_colunas:
            return
        s = doc.add_section(WD_SECTION.CONTINUOUS)
        _pagina(s)
        _colunas(s, n_colunas)
        estado['colunas'] = n_colunas

    for bloco in blocos:
        tipo = bloco[0]
        if tipo == 'resumo':
            p = _par(doc, depois=6)
            r1 = p.add_run('Resumo—')
            r1.font.size, r1.font.bold, r1.font.italic = Pt(9), True, True
            r2 = p.add_run(bloco[1])
            r2.font.size, r2.font.bold = Pt(9), True
        elif tipo == 'chaves':
            p = _par(doc, depois=10)
            r1 = p.add_run('Palavras-chave—')
            r1.font.size, r1.font.bold, r1.font.italic = Pt(9), True, True
            r2 = p.add_run(bloco[1])
            r2.font.size, r2.font.bold = Pt(9), True
        elif tipo == 'h1':
            voltar_para(2)
            estado['h1'] += 1
            estado['h2'] = 0
            _par(doc, f'{ROMANOS[estado["h1"] - 1]}.  {bloco[1]}', tamanho=10, versalete=True,
                 alinhamento=WD_ALIGN_PARAGRAPH.CENTER, antes=11, depois=3)
        elif tipo == 'h2':
            voltar_para(2)
            estado['h2'] += 1
            _par(doc, f'{chr(64 + estado["h2"])}. {bloco[1]}', tamanho=10, italico=True,
                 alinhamento=WD_ALIGN_PARAGRAPH.LEFT, antes=6, depois=2)
        elif tipo == 'p':
            voltar_para(2)
            _par(doc, bloco[1], tamanho=10, recuo=0.17)
        elif tipo == 'fig':
            voltar_para(2)
            estado['fig'] += 1
            caminho_fig = _caminho_figura(bloco[1], bloco[3])
            p = _par(doc, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, antes=6, depois=2)
            largura = LARGURA_FIGURA.get(bloco[1], LARGURA_COLUNA)
            p.add_run().add_picture(str(caminho_fig), width=Inches(largura))
            p.paragraph_format.keep_with_next = True      # a legenda acompanha a figura
            _par(doc, f'Fig. {estado["fig"]}.  {bloco[2]}', tamanho=8,
                 alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, depois=8)
        elif tipo == 'tab':
            estado['tab'] += 1
            spec = TABELAS.get(bloco[1], {})
            larga = spec.get('largura_total', False)
            voltar_para(1 if larga else 2)
            cab = _par(doc, f'TABELA {ROMANOS[estado["tab"] - 1]}', tamanho=8, versalete=True,
                       alinhamento=WD_ALIGN_PARAGRAPH.CENTER, antes=8, depois=1)
            leg = _par(doc, bloco[2], tamanho=8, alinhamento=WD_ALIGN_PARAGRAPH.CENTER, depois=3)
            cab.paragraph_format.keep_with_next = True
            leg.paragraph_format.keep_with_next = True
            _tabela_docx(doc, _dados_tabela(res, bloco[1]), spec, larga)
            _par(doc, '', depois=8)

    # Referências: título sem numeração romana, como no IEEEtran.
    voltar_para(2)
    _par(doc, 'Referências', tamanho=10, versalete=True,
         alinhamento=WD_ALIGN_PARAGRAPH.CENTER, antes=11, depois=4)
    for i, ref in enumerate(rb.REFERENCIAS, start=1):
        p = _par(doc, depois=2)
        pf = p.paragraph_format
        pf.left_indent, pf.first_line_indent = Inches(0.2), Inches(-0.2)
        r = p.add_run(f'[{i}]\t{ref}')
        r.font.size, r.font.name = Pt(8), 'Times New Roman'

    _rodape_primeira_pagina(doc)
    return doc


def _rodape_primeira_pagina(doc):
    """Link do repositório no rodapé da primeira página (exigência de reprodutibilidade).

    Só agora, com todas as seções criadas: `add_section()` clona a seção corrente e devolve
    sempre o mesmo elemento de base, então `doc.sections[0]` só aponta para a primeira seção
    de verdade depois que o documento está montado. O rodapé vai nas duas seções da página 1,
    porque o leitor usa a seção em que a página termina.
    """
    texto = (f'Código e dados para reprodução: {rb.REPOSITORIO} '
             f'(random_state = {pp.RANDOM_STATE} em todas as etapas).')
    for s in doc.sections[:2]:
        s.different_first_page_header_footer = True
        rodape = s.first_page_footer
        rodape.is_linked_to_previous = False
        p = rodape.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(texto)
        r.font.size, r.font.name = Pt(8), 'Times New Roman'
    # Nas demais seções, "primeira página diferente" faria o rodapé reaparecer no meio do artigo.
    for s in doc.sections[2:]:
        s.different_first_page_header_footer = False


def _caminho_figura(nome, origem):
    if origem == 'A1':
        return RAIZ / 'Análise Bivariada' / 'figuras' / f'{nome}.png'
    return RAIZ / 'Modelagem_A2' / 'figuras' / f'{nome}.png'


def _dados_tabela(res, nome):
    spec = TABELAS.get(nome, {})
    df = pd.read_csv(res.tab / f'{nome}.csv')
    if nome == 'regua_vazamento':
        # Um cenário por bloco de linhas: nome e número de atributos aparecem só na primeira, para
        # a tabela não repetir a mesma informação três vezes seguidas.
        df = df.copy()
        repetida = df['cenário'].duplicated()
        df['cenário'] = df['cenário'].str.replace(r' \(\d+\)$', '', regex=True)
        df['atributos'] = df['atributos'].astype(str)
        df.loc[repetida, ['cenário', 'atributos']] = ''
    if 'modelo' in df.columns:
        df = df.replace({'modelo': ABREVIAR_MODELO})
    if 'colunas' in spec:
        df = df[spec['colunas']]
    if 'renomear' in spec:
        df = df.rename(columns=spec['renomear'])
    df.columns = [str(c) if not str(c).startswith('Unnamed') else '' for c in df.columns]
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        # Numa mesma coluna, todos os valores com a mesma quantidade de casas: "60" ao lado de
        # "41,8" parece erro de digitação, não arredondamento.
        valores = df[col].dropna()
        if len(valores) and not (valores % 1 == 0).all():
            casas = 1 if valores.abs().max() >= 10 else 3
            df[col] = df[col].map(lambda x, c=casas: '' if pd.isna(x)
                                  else f'{x:.{c}f}'.replace('.', ','))
        else:
            df[col] = df[col].map(_num_br)
    return df.astype(str).replace('nan', '')


def _num_br(x):
    """Número no padrão brasileiro: vírgula decimal e ponto de milhar."""
    if pd.isna(x):
        return ''
    if float(x).is_integer() and abs(x) >= 1000:
        return f'{int(x):,}'.replace(',', '.')
    if float(x).is_integer():
        return str(int(x))
    return (f'{x:.3f}' if abs(x) < 10 else f'{x:.1f}').replace('.', ',')


def _nao_quebrar(linha, com_a_proxima=True):
    """Mantém a linha inteira numa página só e, se pedido, junto da linha seguinte."""
    trPr = linha._tr.get_or_add_trPr()
    trPr.append(OxmlElement('w:cantSplit'))
    for cel in linha.cells:
        for p in cel.paragraphs:
            p.paragraph_format.keep_with_next = com_a_proxima


def _layout_fixo(t, larguras):
    """Larguras explícitas e margens de célula estreitas.

    Sem isto, o cálculo automático de largura estoura a coluna de 3,5 pol e as primeiras
    colunas da tabela somem na conversão para PDF.
    """
    t.autofit = False                       # a própria API escreve <w:tblLayout w:type="fixed">
    tblPr = t._tbl.tblPr
    # A grade da tabela é quem manda no layout fixo. O python-docx a cria com a largura do
    # texto da PÁGINA (7,25 pol), que é o dobro de uma coluna do artigo.
    grade = t._tbl.find(qn('w:tblGrid'))
    for col, largura in zip(grade.findall(qn('w:gridCol')), larguras):
        col.set(qn('w:w'), str(int(round(largura * 1440))))
    larg_total = tblPr.find(qn('w:tblW'))
    if larg_total is not None:
        larg_total.set(qn('w:type'), 'dxa')
        larg_total.set(qn('w:w'), str(int(round(sum(larguras) * 1440))))
    margens = OxmlElement('w:tblCellMar')
    for lado in ('left', 'right'):
        m = OxmlElement(f'w:{lado}')
        m.set(qn('w:w'), '40')          # 40 twips = 0,028 pol
        m.set(qn('w:type'), 'dxa')
        margens.append(m)
    tblPr.append(margens)
    for linha in t.rows:
        for cel, largura in zip(linha.cells, larguras):
            cel.width = Inches(largura)


def _tabela_docx(doc, df, spec, larga):
    tamanho = Pt(spec.get('fonte', 8))
    t = doc.add_table(rows=len(df) + 1, cols=len(df.columns))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for j, col in enumerate(df.columns):
        cel = t.cell(0, j)
        cel.text = ''
        p = cel.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(str(col))
        r.font.size, r.font.bold, r.font.name = tamanho, True, 'Times New Roman'
        _borda(cel._tc, ['top', 'bottom'])
    for i, (_, linha) in enumerate(df.iterrows(), start=1):
        for j, valor in enumerate(linha):
            cel = t.cell(i, j)
            cel.text = ''
            p = cel.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j < 2 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(valor))
            r.font.size, r.font.name = tamanho, 'Times New Roman'
            _borda(cel._tc, ['bottom'] if i == len(df) else [])
    if spec.get('larguras'):
        _layout_fixo(t, spec['larguras'])
    # A tabela não se parte entre páginas: a última linha órfã numa página seguinte
    # é um dos defeitos de diagramação mais visíveis num artigo de duas colunas.
    for i, linha in enumerate(t.rows):
        _nao_quebrar(linha, com_a_proxima=i < len(t.rows) - 1)
    return t


# -------------------------------------------------------------------- LaTeX
# Primeiro escapam-se os caracteres reservados do LaTeX; só depois entram os comandos dos
# símbolos. Na ordem inversa, as barras e cifrões dos próprios comandos seriam escapados.
RESERVADOS_TEX = [('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'), ('$', r'\$'),
                  ('#', r'\#'), ('_', r'\_'), ('{', r'\{'), ('}', r'\}'),
                  ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')]
SIMBOLOS_TEX = [('×', r'$\times$'), ('−', r'$-$'), ('≥', r'$\ge$'), ('≤', r'$\le$'),
                ('ρ', r'$\rho$'), ('≈', r'$\approx$'), ('→', r'$\rightarrow$'),
                ('—', '---'), ('–', '--'), ('…', r'\ldots{}'), ('|', r'\textbar{}'),
                ('“', '``'), ('”', "''")]


def tex(texto):
    saida = str(texto)
    for de, para in RESERVADOS_TEX:
        saida = saida.replace(de, para)
    saida = re.sub(r'"([^"]*)"', r"``\1''", saida)      # aspas retas viram aspas do LaTeX
    for de, para in SIMBOLOS_TEX:
        saida = saida.replace(de, para)
    # Por último, depois de todo o escape: *trecho* vira itálico, como no DOCX.
    return re.sub(r'\*(.+?)\*', r'\\textit{\1}', saida)


def gerar_tex(blocos, res, caminho):
    L = []
    A = L.append
    A(r'% Relatório da Avaliação A2 — gerado por Modelagem_A2/gerar_relatorio_A2.py')
    A(r'% Compilar no Overleaf (pdfLaTeX) com o template oficial IEEEtran.')
    A(r'\documentclass[conference]{IEEEtran}')
    A(r'\IEEEoverridecommandlockouts')
    A(r'\usepackage[utf8]{inputenc}')
    A(r'\usepackage[T1]{fontenc}')
    A(r'\usepackage[brazil]{babel}')
    A(r'\usepackage{graphicx,amsmath,booktabs,url}')
    A(r'\graphicspath{{Modelagem_A2/figuras/}}')
    A(r'\begin{document}')
    A(r'\title{' + tex(rb.TITULO) + '}')
    A(r'\author{\IEEEauthorblockN{' + tex(', '.join(rb.AUTORAS)) + r'}' +
      r'\IEEEauthorblockA{' + tex(rb.AFILIACAO) + r'\\' + tex(rb.DISCIPLINA) + r'}' +
      r'\thanks{Código e dados para reprodução: \url{' + rb.REPOSITORIO +
      r'} (random\_state = ' + str(pp.RANDOM_STATE) + r' em todas as etapas).}}')
    A(r'\maketitle')

    n_fig = n_tab = 0
    for bloco in blocos:
        tipo = bloco[0]
        if tipo == 'resumo':
            A(r'\begin{abstract}')
            A(tex(bloco[1]))
            A(r'\end{abstract}')
        elif tipo == 'chaves':
            A(r'\begin{IEEEkeywords}')
            A(tex(bloco[1]))
            A(r'\end{IEEEkeywords}')
        elif tipo == 'h1':
            A(r'\section{' + tex(bloco[1]) + '}')
        elif tipo == 'h2':
            A(r'\subsection{' + tex(bloco[1]) + '}')
        elif tipo == 'p':
            A(tex(bloco[1]))
            A('')
        elif tipo == 'fig':
            n_fig += 1
            A(r'\begin{figure}[!t]')
            A(r'\centering')
            fracao = LARGURA_FIGURA.get(bloco[1], LARGURA_COLUNA) / LARGURA_COLUNA
            medida = r'\columnwidth' if fracao >= 0.99 else f'{fracao:.2f}' + r'\columnwidth'
            A(r'\includegraphics[width=' + medida + ']{' + bloco[1] + '}')
            A(r'\caption{' + tex(bloco[2]) + '}')
            A(r'\label{fig:' + bloco[1] + '}')
            A(r'\end{figure}')
        elif tipo == 'tab':
            n_tab += 1
            spec = TABELAS.get(bloco[1], {})
            larga = spec.get('largura_total', False)
            df = _dados_tabela(res, bloco[1])
            amb = 'table*' if larga else 'table'
            A(r'\begin{' + amb + r'}[!t]')
            A(r'\caption{' + tex(bloco[2]) + '}')
            A(r'\label{tab:' + bloco[1] + '}')
            A(r'\centering')
            A(r'\footnotesize' if larga else r'\small')
            A(r'\begin{tabular}{' + 'l' * 2 + 'c' * (len(df.columns) - 2) + '}')
            A(r'\toprule')
            A(' & '.join(tex(c) for c in df.columns) + r' \\')
            A(r'\midrule')
            for _, linha in df.iterrows():
                A(' & '.join(tex(x) for x in linha) + r' \\')
            A(r'\bottomrule')
            A(r'\end{tabular}')
            A(r'\end{' + amb + '}')

    A(r'\begin{thebibliography}{00}')
    for i, ref in enumerate(rb.REFERENCIAS, start=1):
        A(r'\bibitem{b' + str(i) + '} ' + tex(ref))
    A(r'\end{thebibliography}')
    A(r'\end{document}')
    caminho.write_text('\n'.join(L), encoding='utf-8')
    return caminho


# ----------------------------------------------------------------- utilidades
def converter_pdf(docx, destino):
    soffice = Path(r'C:\Program Files\LibreOffice\program\soffice.exe')
    if not soffice.exists():
        soffice = Path(shutil.which('soffice') or '')
    if not soffice.exists():
        print('LibreOffice não encontrado: PDF não gerado.')
        return None
    subprocess.run([str(soffice), '--headless', '--convert-to', 'pdf', '--outdir',
                    str(destino.parent), str(docx)], check=True, capture_output=True, timeout=300)
    return destino if destino.exists() else None


def contar_paginas(pdf):
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf)).pages)
    except Exception as erro:
        print('não foi possível contar as páginas:', erro)
        return None


def main():
    res = rb.Resultados(RAIZ)
    blocos = resolver_referencias(rb.blocos(res))

    resumo = next(b[1] for b in blocos if b[0] == 'resumo')
    palavras = len(re.findall(r'\S+', resumo))
    print(f'cenário principal: {rb.CENARIO_PRINCIPAL} | modelo escolhido na validação cruzada: '
          f'{res.melhor} | de maior AUC no teste: {res.melhor_teste}')
    print(f'resumo: {palavras} palavras (exigido: 100 a 150)'
          + ('  OK' if 100 <= palavras <= 150 else '  >>> FORA DA FAIXA <<<'))

    doc = gerar_docx(blocos, res, SAIDA_DOCX)
    doc.save(SAIDA_DOCX)
    print('DOCX:', SAIDA_DOCX.relative_to(RAIZ))

    gerar_tex(blocos, res, SAIDA_TEX)
    print('TEX :', SAIDA_TEX.relative_to(RAIZ))

    pdf = converter_pdf(SAIDA_DOCX, SAIDA_PDF)
    if pdf:
        n = contar_paginas(pdf)
        print(f'PDF : {pdf.relative_to(RAIZ)} — {n} páginas'
              + ('  OK' if n and n <= MAX_PAGINAS else f'  >>> ACIMA DE {MAX_PAGINAS} <<<'))
    n_fig = sum(1 for b in blocos if b[0] == 'fig')
    n_tab = sum(1 for b in blocos if b[0] == 'tab')
    print(f'figuras: {n_fig} | tabelas: {n_tab} | referências: {len(rb.REFERENCIAS)}')


if __name__ == '__main__':
    main()
