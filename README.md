# Atividade avaliativa da disciplina de Mineração de Dados

## Discentes: Jamily Vieira, Júlia Souza, Jessyca Rodrigues e Yasmin Mageste

Estudo de caso *Condição cardíaca de crianças e adolescentes*: preparação e análise exploratória de uma base de consultas de cardiologia pediátrica (Avaliação A1: pré-processamento, limpeza e transformação) e modelagem preditiva do laudo (Avaliação A2: classificação Normal × Anormal).

## Base de dados

`UCMF_raw.csv` reúne 12.873 consultas cardiológicas pediátricas da Unidade de Cardiologia e Medicina Fetal (UCMF) do Real Hospital Português, em Recife-PE, anonimizadas com aprovação do Comitê de Ética do RHP, conforme a descrição do estudo de caso. São 21 colunas: medidas antropométricas, datas, pressão arterial, achados do exame físico, histórico da doença, sexo e motivo do encaminhamento.

- **Variável-alvo:** `NORMAL X ANORMAL`.
- **População:** 0 a 19 anos, recorte definido pelo professor no escopo do trabalho e registrado na tabela-mestra (`Docs/tabela-mestra-corrigida.xlsx`). A Academia Americana de Pediatria estende a idade-limite da pediatria até 21 anos (AAP, 1988); usar 0–21 manteria 27 pacientes a mais na base limpa.

O dicionário de variáveis (tipo, unidade, faixa plausível e papel) está em `Docs/tabela-mestra-corrigida.xlsx`.

## Estrutura do repositório

```
mineracao_de_dados/
├── UCMF_raw.csv                       base original (não é alterada)
├── requirements.txt                   dependências (versões testadas)
├── RESUMO_DAS_ALTERACOES.md           o que mudou na mescla e por quê
├── decisoes_equipe_A2.md              decisões metodológicas do grupo na A2
├── Docs/
│   ├── tabela-mestra-corrigida.xlsx   dicionário de variáveis
│   ├── levantamento_qualidade_UCMFnew.xlsx  inventário de problemas de qualidade
│   ├── regra_conversao.csv            regras de conversão (gerada pela análise univariada)
│   └── cdc/                           tabelas LMS do CDC usadas na limpeza (cópia local)
├── Análise Univariada/
│   ├── análise_univariada.ipynb
│   ├── fig1_histogramas.png, fig2_boxplots.png, fig3_ausentes.png
│   └── tabela_A.csv, tabela_B.csv, tabela_C.csv   numéricas, categóricas e demais variáveis
├── Limpeza/
│   ├── Limpeza_V1.ipynb               primeira versão (mantida como histórico)
│   ├── Limpeza_V2.ipynb               limpeza atual
│   ├── UCMF_limpo.csv                 base limpa
│   └── antes_depois.csv               % de nulos antes × depois e ação aplicada, por variável
├── Análise Bivariada/
│   ├── analise_bivariada.ipynb        bivariada, evidências e aplicação das transformações
│   ├── figuras/                       gráficos prontos para o relatório (PNG, 300 dpi)
│   ├── tabelas/                       tabelas exportadas para o relatório (CSV)
│   └── modelagem/                     treino.csv, teste.csv e colunas_por_grupo.csv (entrada da A2)
├── Modelagem_A2/                      Avaliação A2 (pasta final)
│   ├── preprocessamento.py            PreprocessadorUCMF (o mesmo da A1) no formato do scikit-learn
│   ├── modelagem_A2.ipynb             notebook da modelagem, com as saídas gravadas
│   ├── gerar_relatorio_A2.py          gera a base do relatório a partir das tabelas exportadas
│   ├── figuras/                       figuras do artigo (PNG, 600 dpi, largura final da coluna)
│   └── tabelas/                       métricas, matriz de confusão, importâncias, deriva temporal
├── relatorio_A2.docx / .pdf / .tex    base do relatório da A2, gerada por gerar_relatorio_A2.py
└── relatorio_A2_corrigido.docx / .tex versão final revisada do relatório da A2 (a submetida)
```

tudo o que o relatório usa está em `Modelagem_A2/`.

## Como executar

1. **Ambiente:** Python 3.11 ou superior (testado com 3.13.3):
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Windows)   |   source .venv/bin/activate   (Linux/macOS)
   pip install -r requirements.txt
   ```
   O matplotlib precisa ser 3.10 ou mais recente (`boxplot(orientation="horizontal")`).
2. **Ordem dos notebooks**, porque cada um usa o resultado do anterior:
   1. `Análise Univariada/análise_univariada.ipynb`
   2. `Limpeza/Limpeza_V2.ipynb`, que gera `Limpeza/UCMF_limpo.csv` e `Limpeza/antes_depois.csv`
   3. `Análise Bivariada/analise_bivariada.ipynb`, que lê `UCMF_limpo.csv`
   4. a modelagem da A2, em `Modelagem_A2/` — dois passos, na seção "Avaliação A2" mais abaixo
3. **Tabelas do CDC (internet):** a `Limpeza_V2` usa as tabelas de crescimento do CDC nas Etapas 4.1 e 6. Elas já estão em `Docs/cdc/`, então o notebook roda sem internet. Se a pasta for apagada, o notebook baixa de novo: primeiro do site oficial e, se ele falhar, de um espelho (`restoredcdc.org`). Em 28/09/2026 o site oficial respondeu HTTP 403, e as tabelas vieram do espelho; a base limpa gerada com elas é idêntica à original da Júlia.

Os caminhos são resolvidos automaticamente: cada notebook localiza a pasta do projeto procurando o `UCMF_raw.csv`. Por isso funcionam tanto abertos na própria pasta quanto a partir da raiz.

## Limpeza (`Limpeza/Limpeza_V2.ipynb`)

As etapas seguem uma ordem fixa, porque cada uma depende das anteriores:

| Etapa | O que faz |
|---|---|
| 1. Padronização das categóricas | Unifica grafias com dicionários explícitos. Converte códigos de ausência ("Não Calculado", "#VALUE!", "Indeterminado") em nulo. Remove `Convenio`. |
| 2. FC | Converte para número. Faixas como "80-90" viram o ponto médio. |
| 3. Limites | Valores fisicamente impossíveis viram nulo: 0 em Peso e Altura, limites fixos para Peso, Altura, FC e PA, e PAS ≤ PAD. |
| 4. IDADE | Recalcula a idade pelas datas (inclusive as gravadas como serial do Excel). A idade da planilha usava dias ÷ 352. Remove idades fora de 0–19 anos e cria `grupo_paciente`. |
| 4.1 Curvas do CDC | Peso e Altura implausíveis para a idade e o sexo (z-score modificado do CDC 2000) viram nulo. Linhas em que os dois são implausíveis no mesmo sentido saem, porque indicam idade errada. |
| 5. IMC | Recalculado a partir de Peso e Altura já validados. |
| 6. PPA | Reclassificada pelo *Fourth Report* (2004), com coeficientes conferidos com a Tabela B-1 do relatório. A PPA original serve só de validação. |
| 7. HDA e MOTIVO | Viram colunas binárias (`sint_*`, `motivo_*`) e indicadores de ausência. |
| 8. Ausência de PA | Cria `pa_medida`. A falta de PA não é aleatória: se concentra nos pacientes mais novos. |
| 9. Deduplicação | Remove linhas idênticas, sem considerar o ID (103 linhas). A univariada conta 987 duplicatas no bruto, mas 890 delas são registros quase vazios, sem IDADE, que já saíram na Etapa 4. |
| 10. Remoções finais | Remove linhas sem alvo ou com 6 ou mais de 10 atributos ausentes. |

**Resultado:** `UCMF_limpo.csv`, com 10.576 linhas e 51 colunas (57,6% Normal / 42,4% Anormal). Nenhuma imputação foi feita; ela fica para depois da divisão treino/teste, para evitar vazamento de dados.

## Análise bivariada e transformações (`Análise Bivariada/analise_bivariada.ipynb`)

- **Parte 1 – FC × IDADE:** compara antes e depois da limpeza e mostra a relação na base limpa (Spearman). Complemento: IDADE × Peso, que mostra por que Peso e Altura são redundantes com a IDADE.
- **Parte 2 – Cada variável × alvo:** qui-quadrado (α = 0,05), com as numéricas divididas em quartis. Um único teste para todas as variáveis deixa os resultados comparáveis numa só tabela. O efeito é resumido pela diferença de % Anormal entre a categoria de maior e a de menor proporção. Dois cuidados na leitura:
  - quando a relação não é monotônica, a maior e a menor proporção não estão nos quartis extremos (na PA sistólica, o resumo compara Q1 com Q2), e a coluna "observação" avisa;
  - quando muitos valores se repetem, dois quartis se fundem numa faixa só (na PA diastólica, "Q1–Q2").
- **Parte 2.1 – Tamanho de efeito:** |r| de Mann-Whitney para as numéricas e V de Cramér para as categóricas, sem discretizar e sem depender do n.
- **Parte 3 – Confundimento FC × IDADE:** compara a FC bruta com a FC padronizada dentro de cada faixa etária, em quartis e em |r|.
- **Parte 3.1 – Ausência de PA × idade:** % de Anormal com e sem PA dentro de cada faixa etária e *odds ratio* de Mantel-Haenszel.
- **Parte 4 – Evidências para as transformações:** correlações, assimetria, categorias raras e balanceamento do alvo, em `tabelas/transformacoes.csv`.
- **Parte 5 – Acréscimos à tabela:** risco de vazamento, colunas binárias raras, `pa_medida` como *proxy* da idade, imputação por faixa etária, PPA ordinal e divisão por paciente, em `tabelas/transformacoes_completa.csv`.
- **Parte 6 – Pré-processador:** `PreprocessadorUCMF` aprende medianas, médias, desvios e categorias **só no treino** e aplica ao teste. A divisão é estratificada pelo alvo e agrupada por `grupo_paciente`. Exporta `modelagem/treino.csv`, `modelagem/teste.csv` e `modelagem/colunas_por_grupo.csv`.

## Cuidados para a modelagem

- **`grupo_paciente` (descartada na A2):** a coluna agrupa linhas com a mesma data de atendimento e a mesma data de nascimento, e a A1 a tratava como identificador de paciente. A verificação feita na A2 mostrou que a suposição não se sustenta: dos 160 grupos com mais de uma linha, **31 reúnem registros de sexos diferentes** e 42 reúnem laudos diferentes — são crianças distintas atendidas no mesmo dia. A base não tem identificador de paciente. Na A2, cada linha é tratada como uma consulta independente, e a coluna não é usada nem como variável nem para agrupar a divisão. O mesmo vale para `ID`.
- **Parâmetros aprendidos:** imputação, padronização e z-score por faixa etária devem ser calculados **apenas no conjunto de treino** (na validação cruzada, dentro de cada dobra).
- **Nulos da `PPA_calc`:** 76% de nulos, porque a PA não foi medida. A ausência deve virar uma categoria própria, não ser preenchida pela moda.
- **Colunas a descartar:** `PPA_PAS_calc`, `PPA_PAD_calc` e `z_altura` são intermediárias do cálculo da PPA, e `numero de episodios` repete a informação das colunas `sint_*`. A justificativa está em `tabelas/transformacoes.csv`.
- **Vazamento de informação:** SOPRO, B2 e PULSOS são anotados no mesmo exame que produz o laudo e foram **excluídos na A2** (10 colunas codificadas). O motivo do encaminhamento foi **mantido**: é escrito por outro médico antes da consulta e, portanto, está disponível numa triagem — das 2.122 crianças encaminhadas por sopro, o cardiologista confirmou o achado em 78%, e das 3.994 com sopro no exame só 41% vinham encaminhadas por sopro. `modelagem/colunas_por_grupo.csv` permite montar os três cenários comparados no relatório (47, 37 e 19 atributos).
- **`pa_medida`:** funciona como *proxy* da idade (OR ajustado por faixa etária ≈ 1); não indica doença.

## Material para o relatório 

| Seção | Arquivos |
|---|---|
| Univariada quantitativa | `Análise Univariada/tabela_A.csv`, `fig1_histogramas.png`, `fig2_boxplots.png` |
| Univariada categórica e ausentes | `tabela_B.csv`, `tabela_C.csv`, `fig3_ausentes.png` |
| Problemas × soluções | `Limpeza/antes_depois.csv`, `Docs/regra_conversao.csv` |
| Duas variáveis (FC × IDADE) | `figuras/fc_idade_antes_depois.png`, `figuras/fc_por_faixa_etaria.png`, `tabelas/fc_por_faixa.csv`, `figuras/idade_peso.png` |
| Bivariada com o alvo | `figuras/bivariada_categoricas.png`, `figuras/bivariada_numericas.png`, `figuras/forca_associacao.png`, `tabelas/bivariada_resumo.csv` |
| Transformações | `tabelas/transformacoes_completa.csv`, `figuras/correlacao_antropometricas.png`, `figuras/pa_ausente_por_idade.png` |

## Avaliação A2 — modelagem (`Modelagem_A2/`)

**Tarefa:** classificação binária de `NORMAL X ANORMAL`. Entrada: `Limpeza/UCMF_limpo.csv`.

**Ordem de execução** (a partir da raiz do projeto, com o `.venv` ativado):

1. **`Modelagem_A2/modelagem_A2.ipynb`** — a modelagem inteira: divisão, validação cruzada,
   avaliação no teste, importâncias, régua do vazamento, deriva temporal, figuras e tabelas.
   Pode ser aberto no VS Code ou executado pela linha de comando:
   ```bash
   jupyter nbconvert --execute --inplace "Modelagem_A2/modelagem_A2.ipynb"
   ```
2. **`python Modelagem_A2/gerar_relatorio_A2.py`** — lê as tabelas do passo anterior e gera
   `relatorio_A2.docx`, `.pdf` e `.tex`.

**Use o kernel do `.venv`** (no VS Code, selecione o interpretador `.venv`): se houver um kernel
`python3` registrado no perfil do usuário, ele tem precedência sobre o do ambiente e a execução
falha com `ModuleNotFoundError`, mesmo terminando com código de saída 0. A modelagem leva de 3 a 12
minutos, conforme a carga da máquina. Ao encerrar, o `joblib` pode imprimir um `KeyError` sobre uma
pasta temporária: é da limpeza dos processos paralelos no Windows, não da análise.

**Reprodutibilidade:** `random_state = 42` em todas as etapas (divisão, dobras, florestas, gradient
boosting, regressão logística, permutações e *bootstrap*). Rodar os dois passos acima na mesma
ordem reproduz todos os números do relatório. O pré-processador é conferido contra as matrizes
exportadas na A1 (`Análise Bivariada/modelagem/treino.csv` e `teste.csv`): a diferença máxima é de
2×10⁻¹⁵, só arredondamento do CSV.

**Decisões de protocolo** (as duas primeiras corrigem o que a A1 havia previsto):

- **Sem `grupo_paciente`:** a chave não identifica paciente (ver "Cuidados para a modelagem").
  Cada consulta é tratada como observação independente, e a divisão é `StratifiedKFold`, sem
  agrupamento. O custo é pequeno e está medido: sem agrupar, apenas 53 dos 10.407 grupos caem dos
  dois lados da divisão.
- **Vazamento:** excluídos os **três achados do exame físico** (SOPRO, B2 e PULSOS — 10 colunas),
  e não apenas o sopro. O critério é a origem da informação, não a força da associação. O motivo
  do encaminhamento é mantido, por ser anterior à consulta.
- **Divisão 80/20 estratificada**, tomada como a primeira partição de um `StratifiedKFold` de 5 —
  não um corte solto. Hiperparâmetros, escolha do modelo e limiar saem de **validação cruzada de 5
  dobras dentro do treino**; o teste é aberto uma única vez, no fim.
- **Confirmação independente:** validação cruzada aninhada 5×3 sobre as 10.576 consultas, que não
  depende de um corte específico. É a estimativa que o relatório adota como desempenho esperado.
- **Pré-processamento dentro do fluxo:** `PreprocessadorUCMF` é um passo do `Pipeline`, reajustado
  dentro de cada dobra. Nenhuma estatística da parte de validação participa do ajuste.
- **Três cenários de atributos:** 47 (com o exame físico — só régua para medir o vazamento),
  **37 (sem o exame físico — cenário principal)** e 19 (sem exame físico e sem motivo). Trocar o
  cenário principal é mudar `CENARIO_PRINCIPAL` em `Modelagem_A2/preprocessamento.py` e em
  `relatorio_blocos.py`, e rodar tudo de novo.
- **Algoritmos:** classe majoritária (piso), regressão logística (baseline simples), floresta
  aleatória e gradient boosting por histogramas (complexos).
- **Ponto de operação:** o limiar é escolhido para sensibilidade 0,80 nas previsões *out-of-fold*
  do treino e só então aplicado ao teste.

**Resultado em uma linha:** a AUC cai de 0,950 com os achados do exame físico para 0,777 sem eles
(validação cruzada); a aninhada na base inteira estima 0,786 ± 0,013. A diferença entre o melhor
modelo complexo e o baseline linear é de 0,012 — catorze vezes menor que o efeito da exclusão do
exame físico.

**Saídas:** `Modelagem_A2/tabelas/` (28 CSVs: métricas por dobra e agregadas, hiperparâmetros,
matriz de confusão, erros por faixa etária e por motivo, limiar, importâncias por grupo e por
coluna, razões de chance, régua do vazamento, deriva temporal e validação cruzada aninhada) e
`Modelagem_A2/figuras/` (PNG a 600 dpi, na largura final de uma coluna ou da página do IEEE).

**Relatório:** `gerar_relatorio_A2.py` produz a base do relatório (`relatorio_A2.docx`, `.pdf` e
`.tex`) no layout de conferência do IEEE (carta, duas colunas, Times New Roman 10 pt), lendo os
números dos CSVs em tempo de geração. Essa base foi depois estruturada e revisada pelo grupo, com
auxílio de IA, e a versão final submetida é `relatorio_A2_corrigido.docx`; o
`relatorio_A2_corrigido.tex` traz o mesmo texto em `\documentclass[conference]{IEEEtran}`, com as
referências na ordem de citação, e pode ser compilado no Overleaf (figuras em
`Modelagem_A2/figuras/`). Rodar o gerador de novo recria a base, não a versão revisada. Os números
da versão final vêm dos CSVs de `Modelagem_A2/tabelas/`, exceto a contagem de registros removidos na
limpeza, que vem da A1 (`Limpeza/Limpeza_V2.ipynb`).

## Referências

- Unidade de Cardiologia e Medicina Fetal (UCMF), Real Hospital Português (RHP). *UCMF_raw: consultas de cardiologia pediátrica* (conjunto de dados anonimizado). Recife-PE. Fornecido pelo professor da disciplina Mineração de Dados, Instituto de Informática, UFG, 2026.
- American Academy of Pediatrics, Council on Child and Adolescent Health. *Age limits of pediatrics*. Pediatrics, 1988; 81(5): 736.
- CDC – *Growth Charts* (2000), tabelas LMS: https://www.cdc.gov/growthcharts/
- National High Blood Pressure Education Program Working Group. *The Fourth Report on the Diagnosis, Evaluation, and Treatment of High Blood Pressure in Children and Adolescents*. Pediatrics, 2004; 114(2 Suppl 4th Report): 555–576.
