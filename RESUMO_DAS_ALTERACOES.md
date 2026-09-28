# Resumo das alterações (28/09/2026)

Mescla do notebook `A1-1/UCMF_A1_Mesclado.ipynb` (Jamily) no repositório da Júlia. A base é o trabalho da Júlia; do `A1-1` vieram apenas os acréscimos (principalmente de transformação) e as correções. Todos os números abaixo saíram das execuções completas dos notebooks, feitas com o `requirements.txt`.

## 1. Decisão do grupo: faixa etária 0–19 anos

- O commit `ddbe7c7` (Jessyca) já tinha trocado `IDADE_MAX` de 21 para 19 na `Limpeza_V2`, mas deixou o restante inconsistente: `UCMF_limpo.csv` ainda era o de 0–21; a bivariada e o README usavam 21; e a troca por "localizar e substituir" gerou frases sem sentido.
- Decisão confirmada: **0–19** (tabela-mestra do professor). A AAP (1988) fica citada como alternativa.
- **Validação:** a nova base é **exatamente** a base 0–21 da Júlia sem os 27 pacientes com mais de 19 anos (mesmas linhas, colunas e valores). Nenhuma outra regra de limpeza muda com o corte.

### Números que mudaram com o corte

| Indicador | 0–21 (antes) | 0–19 (agora) |
|---|---|---|
| Base limpa | 10.603 × 51 | **10.576 × 51** |
| Alvo | 57,7% Normal / 42,3% Anormal (6.113 / 4.490) | **57,6% / 42,4%** (6.091 / 4.485) |
| Removidas por idade fora da faixa (Etapa 4) | 93 | 121 |
| Removidas pelo CDC (Peso e Altura implausíveis no mesmo sentido) | 102 | 101 |
| Etapa 8: média de idade sem × com PA; % Anormal sem × com PA | 2,7 × 8,4; 47,7% × 35,6% | 2,7 × 8,3; 47,7% × 35,7% |
| Pontos impossíveis no bruto (FC × IDADE) | 173 | 203 (a faixa válida ficou mais estreita) |
| Spearman FC × IDADE | −0,693 (n = 9.994) | −0,692 (n = 9.968) |
| Medianas da FC por faixa | 112 / 92 / 86 / 80 / 78 (15–21) | 112 / 92 / 86 / 80 / 78 (15–19) |
| \|r\| da FC: bruta → ajustada pela idade | 0,275 → 0,124 | 0,274 → 0,124 |
| % com PA medida na última faixa | 91,7% (15–21) | 91,6% (15–19) |
| Assimetria da IDADE; % abaixo de 1 ano | 0,79; 24,9% | 0,76; 25,0% |
| Treino / teste | 8.483 / 2.120 (44 colunas) | 8.460 / 2.116 (47 colunas, após a revisão da seção 3.1) |
| Grupos de paciente com mais de uma linha | 161 | 160 |

**Não mudaram:** divisor 352 (IDADE da planilha cerca de 3,8% alta); 83 DN posteriores ao atendimento (12 por erro de século, 71 por digitação); PPA com 92,5% de concordância em 2.056 pacientes e 512 PPAs preenchíveis; 103 duplicatas; 13 linhas na Etapa 10; confundimento da FC de 30,5 → 14,2 p.p.; OR da PA 0,61 (bruto) e 1,09 (ajustado); V de Cramér do SOPRO 0,84; 31 de 40 variáveis com p < 0,05; 0 grupos em comum entre treino e teste; 0 nulos após transformar.

## 2. `Limpeza/Limpeza_V2.ipynb`

| Alteração | Por quê |
|---|---|
| Função `ler_csv_cdc()` no setup: lê de `Docs/cdc/`; se faltar, baixa do site oficial e, se falhar, de um espelho | O cdc.gov respondeu **HTTP 403** em 28/09/2026, e o notebook quebrava na Etapa 4.1. A lógica de limpeza não mudou. |
| `Docs/cdc/` com as 4 tabelas LMS (`wtageinf`, `wtage`, `lenageinf`, `statage`) | Permite rodar sem internet. Vieram do espelho `restoredcdc.org`; com elas, a base 0–21 saiu byte a byte igual à da Júlia. |
| Comentário da Etapa 4.1 reescrito | "jovens de 20 a 19 anos" não fazia sentido; com o corte em 19, todas as idades estão dentro das tabelas do CDC (até 240 meses). |
| "fora de 19" → "fora de 0–19 anos" (tabela antes × depois) e quebra de linha na frase da Etapa 0 | Restos da troca 21 → 19. |
| Conclusão da Etapa 8: 8,4 → 8,3 anos e 35,6% → 35,7% | Números da base 0–19. |
| Nova célula: exporta `Limpeza/antes_depois.csv` | Tabela de problemas × soluções para o relatório. |
| `UCMF_limpo.csv` regenerado (0–19) | Consequência da decisão da faixa etária. A versão 0–21 continua no histórico do git (commit `aa7a18e`). |

## 3. `Análise Bivariada/analise_bivariada.ipynb`

**Ajustes para 0–19 (sem números fixos no código; tudo sai de `FAIXAS`):** faixas `[0, 1, 5, 10, 15, 19]` e rótulo "15–19"; filtro de "pontos impossíveis" com `FAIXAS[-1]`; eixo do histograma da idade; textos da tabela de transformações e do resumo.

**Células novas (vindas do `A1-1`):**

| Parte | Conteúdo | Critério da A1 |
|---|---|---|
| 1 (complemento) | IDADE × Peso (ρ = 0,97), figura `idade_peso.png` | 4–5: comparação de duas variáveis |
| 2.1 | Tamanho de efeito: \|r\| (Mann-Whitney) e V de Cramér, figura `forca_associacao.png` | 6: bivariada com o alvo |
| 3 (complemento) | Confundimento da FC medido também por \|r\| | 6 |
| 3.1 | Ausência de PA × idade (Mantel-Haenszel), figura `pa_ausente_por_idade.png` | 6 e 7 |
| 5 | 6 linhas extras na tabela de transformações → `transformacoes_completa.csv` | 7: transformações com justificativa |
| 6 | `PreprocessadorUCMF` (aprende só no treino), `StratifiedGroupKFold` por `grupo_paciente`, exportação de `modelagem/` e cenários A × B | 7 |

**Interpretações em markdown** (7 blocos), com os números da execução 0–19. Correções em relação ao texto do `A1-1`:

- "A ordem das variáveis é a mesma do qui-quadrado" estava errado: as pontas coincidem, mas MOTIVO1 sobe de 4ª para 2ª, PULSOS cai de 3ª para 4ª e FC e IDADE trocam de posição.
- Os números 35,5% × 47,6% eram atribuídos à Etapa 8, mas são da base limpa; a Etapa 8 mostra 35,7% × 47,7%.

### 3.1 Revisão do pré-processador (Parte 6)

| Problema encontrado | Evidência | Correção |
|---|---|---|
| A coluna `B2_Outro` era sobrescrita pelo indicador de categorias raras e ficava **toda zerada** | A B2 tem a categoria real "Outro" (65 pacientes, 86,2% Anormal); soma de `B2_Outro` era 0 | O grupo das raras passou a se chamar `<var>_raras` e só é criado se houver categoria rara no treino. `B2_Outro` agora soma 65. |
| `PPA_ord = 0` misturava PPA "Normal" com PPA não calculada | 2.002 pacientes têm PA medida mas PPA nula (1.924 sem altura; o Fourth Report só cobre 1–17 anos) | Novo indicador `ppa_calculada` |
| A tabela propunha log(1 + idade), mas o código fazia z-score simples | Assimetria da IDADE 0,76; com log, −0,25 | `IDADE_log_z` (z-score de log(1 + idade)) |
| SEXO nulo era só imputado pela moda | 469 sem sexo têm 53,9% de Anormais, contra 41,9% dos demais | Novo indicador `sexo_ausente` (mesmo raciocínio de `hda_ausente`) |

As três decisões novas ganharam linha própria em `tabelas/transformacoes_completa.csv`, com a evidência calculada pelo código. Resultado: 47 colunas (cenário B, sem exame físico e motivo: 19), 0 nulos, 0 grupos em comum e nenhuma coluna constante.

## 4. Erros encontrados no `A1-1` que **não** foram trazidos

- "80 DN posteriores ao atendimento (12 + 68)": o correto é **83 (12 + 71)**, como já estava no texto original da Júlia. A mesma troca aparece na lista de números do `CLAUDE.md`.
- "92,5% dos 2.057 pacientes": o correto é **2.056**.
- "Desacordos da PPA vêm sobretudo da regra de 120/80": dos 155 desacordos, o maior bloco (54) vem do corte do estágio 2 (a planilha usou p99 sem os +5 mmHg); a regra dos 120/80 explica 39.
- A anotação da Etapa 1 aparecia duplicada no lugar da anotação da Etapa 10.

## 5. Outros arquivos

- `README.md`: faixa 0–19, estrutura nova, `requirements.txt`, nota sobre o CDC, novas partes da bivariada, material para o relatório e autoria de cada parte.
- `requirements.txt`: versões testadas (Python 3.13.3).
- `.venv/` na raiz: ambiente usado na execução (ignorado pelo git).
- Univariada: só reexecutada. Tabelas e `Docs/regra_conversao.csv` ficaram idênticos; os PNGs foram redesenhados.
- `Limpeza/Limpeza_V1.ipynb` aparece modificada apenas nos metadados de kernel, pelo VS Code, ao abrir o arquivo; o código não foi tocado.

## 6. Pendências

- **Convenio** (removido na Etapa 1) e **Peso/Altura fora do modelo** (redundantes com a IDADE): mantidos como estavam; decisão ainda aberta (Fase 3).
- **Pasta `A1-1/`:** tudo o que era útil foi incorporado; excluída a pedido da Jamily em 28/09/2026.
- Nenhum `git commit` foi feito.
