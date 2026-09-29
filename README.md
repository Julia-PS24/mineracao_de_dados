# Atividade avaliativa da disciplina de Mineração de Dados

## Discentes: Jamily Vieira, Jessyca Rodrigues, Júlia Souza e Yasmin Mageste

Preparação e análise exploratória de uma base de consultas de cardiologia pediátrica (Avaliação A1: pré-processamento, limpeza e transformação).

## Base de dados

`UCMF_raw.csv` reúne 12.873 consultas cardiológicas pediátricas do Real Hospital Português (Recife), em 21 colunas: medidas antropométricas, datas, pressão arterial, achados do exame físico, histórico da doença, sexo e motivo do encaminhamento.

- **Variável-alvo:** `NORMAL X ANORMAL`.
- **População:** 0 a 19 anos, como indica a tabela-mestra (`Docs/tabela-mestra-corrigida.xlsx`). A Academia Americana de Pediatria estende a idade-limite da pediatria até 21 anos (AAP, 1988); usar 0–21 manteria 27 pacientes a mais na base limpa.

O dicionário de variáveis (tipo, unidade, faixa plausível e papel) está em `Docs/tabela-mestra-corrigida.xlsx`.

## Estrutura do repositório

```
MD_A1/
├── UCMF_raw.csv                       base original (não é alterada)
├── requirements.txt                   dependências (versões testadas)
├── RESUMO_DAS_ALTERACOES.md           o que mudou na mescla e por quê
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
└── Análise Bivariada/
    ├── analise_bivariada.ipynb        bivariada, evidências e aplicação das transformações
    ├── figuras/                       gráficos prontos para o relatório (PNG, 300 dpi)
    ├── tabelas/                       tabelas exportadas para o relatório (CSV)
    └── modelagem/                     treino.csv, teste.csv e colunas_por_grupo.csv (entrada da A2)
```

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

- **`grupo_paciente`:** identifica linhas do mesmo paciente na mesma consulta. Use-a só para dividir treino e teste por grupo (ex.: `StratifiedGroupKFold`); ela **não** entra como variável do modelo. O mesmo vale para `ID`.
- **Parâmetros aprendidos:** imputação, padronização e z-score por faixa etária devem ser calculados **apenas no conjunto de treino** (na validação cruzada, dentro de cada dobra).
- **Nulos da `PPA_calc`:** 76% de nulos, porque a PA não foi medida. A ausência deve virar uma categoria própria, não ser preenchida pela moda.
- **Colunas a descartar:** `PPA_PAS_calc`, `PPA_PAD_calc` e `z_altura` são intermediárias do cálculo da PPA, e `numero de episodios` repete a informação das colunas `sint_*`. A justificativa está em `tabelas/transformacoes.csv`.
- **Vazamento de informação:** SOPRO, B2, PULSOS e `motivo_*` fazem parte do próprio julgamento Normal/Anormal. `modelagem/colunas_por_grupo.csv` permite comparar o cenário A (todas as colunas) com o cenário B (sem achados do exame físico e sem motivo).
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

## Referências

- American Academy of Pediatrics, Council on Child and Adolescent Health. *Age limits of pediatrics*. Pediatrics, 1988; 81(5): 736.
- CDC – *Growth Charts* (2000), tabelas LMS: https://www.cdc.gov/growthcharts/
- National High Blood Pressure Education Program Working Group. *The Fourth Report on the Diagnosis, Evaluation, and Treatment of High Blood Pressure in Children and Adolescents*. Pediatrics, 2004; 114(2 Suppl 4th Report): 555–576.
