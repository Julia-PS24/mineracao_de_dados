# CONTEXTO

Sou aluna de Mineração de Dados. Estamos fechando a **Avaliação A1 (pré-processamento: limpeza e transformação)** de um estudo de caso sobre **condição cardíaca em crianças e adolescentes** (base UCMF: 12.873 consultas de cardiologia pediátrica, 21 colunas). **Variável-alvo: `NORMAL X ANORMAL`.**

**Prazos:** relatório no SIGAA em **29/09/2026**; apresentações de 30/09 a 07/10/2026.

Responda sempre em **português do Brasil**.

# O QUE JÁ EXISTE

Nesta pasta há um notebook mesclado, `UCMF_A1_Mesclado.ipynb`, e o `UCMF_raw.csv`. Pode haver também o repositório de uma colega (Júlia), com `UCMF_limpo.csv`, os notebooks originais e a pasta `Docs/`.

**PRIMEIRO PASSO OBRIGATÓRIO:** liste a pasta, confirme quais arquivos existem e me diga o que encontrou antes de alterar qualquer coisa.

O notebook mesclado tem 6 partes:
1. Análise univariada (do grupo).
2. Limpeza (da Júlia, `Limpeza_V2`). Baixa tabelas de crescimento do CDC (LMS) e cacheia em `./cdc`.
3. Comparação de duas variáveis: FC × IDADE, e IDADE × Peso como complemento.
4. Bivariada com o alvo: qui-quadrado por quartis (Júlia), tamanho de efeito (|r| e V de Cramér) e "PA ausente × idade" (novos).
5. Transformações com justificativa, mais um `PreprocessadorUCMF` que aprende só no treino.
6. Fechamento e checklist do relatório.

Cada bloco tem uma anotação em markdown (começa com "📝 Anotação"). O notebook tem um campo `metadata.parte` em cada célula, que pode ser ignorado.

# REGRAS DA AVALIAÇÃO A1 (é o que vale nota)

**Relatório:**
- Máximo de **5 folhas**, fonte Times New Roman 12 **ou** Arial 10.
- **Sem trechos de código e sem prints de tela** dos ambientes de desenvolvimento.
- Conteúdo obrigatório:
  1. Análise univariada (descritiva ou gráfica) de **todas** as variáveis.
  2. Problemas de qualidade de cada variável.
  3. Soluções de limpeza para cada problema.
  4. Comparação de duas variáveis após a limpeza.
  5. Interpretação gráfica dessas duas variáveis.
  6. Análise bivariada entre as variáveis independentes e a variável-alvo, com interpretação.
  7. Transformações a realizar no conjunto de dados, com justificativa.

**Apresentação:** 15 minutos, slides padronizados, numerados, com pouco texto e elementos legíveis. Todos do grupo apresentam e qualquer um pode ser sorteado para responder.

**Critérios:** relatório 50% (tamanho, correção e completude), apresentação 30%, segurança nas respostas 20%.

# TAREFAS (execute em ordem; pare e me pergunte onde indicado)

## Fase 0 — Ambiente
- Crie um venv e instale: `pandas numpy matplotlib seaborn scipy scikit-learn jupyter nbconvert nbformat ipykernel`.
- **Exija matplotlib ≥ 3.10.** O código da colega usa `boxplot(orientation="horizontal")`, que não existe em versões antigas. Mostre as versões instaladas.

## Fase 1 — Executar o notebook de ponta a ponta
- Rode `UCMF_A1_Mesclado.ipynb` inteiro (`jupyter nbconvert --execute`, salvando uma cópia executada). Precisa de **internet** para baixar as tabelas do CDC (`wtageinf.csv`, `wtage.csv`, `lenageinf.csv`, `statage.csv`). Elas ficam em `./cdc`. Se o site oficial falhar, o código tenta um espelho (`restoredcdc.org`).
- **Checagem-chave:** o `UCMF_limpo.csv` gerado deve ter **10.603 linhas × 51 colunas**, com **57,7% Normal / 42,3% Anormal**.
  - Se existir um `UCMF_limpo.csv` de referência da Júlia, compare os dois (mesmas linhas, mesmas colunas, mesmos valores).
  - **Se divergirem, NÃO force o resultado.** Investigue a causa (versão do pandas, versão da tabela do CDC, arredondamento) e me explique.
- Em caso de erro de execução, corrija o mínimo necessário, registre a alteração e não mude a lógica de limpeza.

## Fase 2 — Conferir os números escritos nas anotações
As anotações do notebook citam números de uma execução de referência. Compare cada um com a saída real e corrija o texto onde divergir. Números a conferir:
- **Idade:** a mediana de `dias/IDADE` é 352, e a idade da planilha fica ~3,8% acima da real.
- **CDC:** 102 linhas removidas por Peso e Altura implausíveis no mesmo sentido.
- **PPA:** concordância de 92,5% entre a PPA da planilha e a recalculada; 512 PPAs preenchidas; 1.496 `#VALUE!` coincidem com 1.496 IDADEs vazias.
- **Datas:** 80 DN posteriores ao atendimento (12 por erro de século, 68 por digitação).
- **Duplicatas:** 103 removidas na Etapa 9.
- **Linhas finais:** 13 removidas na Etapa 10.
- **FC × IDADE:** 173 pontos impossíveis no bruto; Spearman ρ = −0,69; medianas por faixa de 112, 92, 86, 80 e 78 bpm.
- **Confundimento da FC:** 30,5 → 14,2 p.p. (quartis) e |r| 0,275 → 0,124.
- **PA ausente:** OR bruto 0,61 e ajustado (Mantel-Haenszel) 1,09; 3,9% com PA na faixa 0–1 ano contra 91,7% aos 15–21.
- **Associação com o alvo:** V de Cramér do SOPRO ≈ 0,84; 31 de 40 variáveis com p < 0,05.
- **Pré-processador:** divisão treino/teste com 0 grupos em comum e 0 nulos após transformar.

**Regra geral:** todo número que aparecer no relatório ou nos slides precisa vir de uma saída que você viu rodando. Não invente nem arredonde "de cabeça".

## Fase 3 — Decisões pendentes (NÃO decida sozinho: pergunte)
1. **Faixa etária:** a limpeza usa 0–21 anos (AAP, 1988), e a tabela-mestra do professor indica 0–19. Afeta ~27 pacientes.
2. **`Convenio`:** a limpeza remove a coluna (32% ausente, siglas inconsistentes, V de Cramér ≈ 0,13). Eu não queria excluir colunas.
3. **Peso e Altura:** saem do modelo por redundância com a IDADE (ρ ≥ 0,97).
Para cada item, dê uma recomendação com prós e contras e espere minha escolha antes de mudar o código.

## Fase 4 — Relatório (DOCX e PDF)
- Use as figuras (`figuras/`, `fig1..3`) e as tabelas (`tabelas/`, `tabela_A/B/C`) geradas pelo notebook. **Sem código e sem prints de terminal ou notebook.**
- Máximo de 5 folhas. **Confira o número de páginas** convertendo para PDF e contando. Se passar, condense tabelas (mostre as principais) e reduza figuras, sem cortar nenhum dos 7 itens obrigatórios.
- Estrutura sugerida:
  - Introdução curta.
  - Univariada quantitativa.
  - Univariada categórica e ausentes.
  - Problemas × soluções (tabela compacta).
  - FC × IDADE (antes × depois, com interpretação).
  - Bivariada com o alvo (com interpretação).
  - Transformações e justificativas.
  - Limitações.
- Figuras e tabelas numeradas, com legenda e chamada no texto. Escrita formal, objetiva, em terceira pessoa.
- Cite: AAP (1988), CDC Growth Charts (2000) e Fourth Report (2004).
- Pontos que **devem** aparecer:
  - A idade da planilha usava ÷ 352.
  - CDC para Peso/Altura, por idade e sexo.
  - PPA recalculada.
  - `grupo_paciente` e divisão treino/teste por paciente.
  - Nenhuma imputação antes da divisão treino/teste.
  - **Risco de vazamento de informação:** SOPRO, B2, PULSOS e `motivo_*` fazem parte do julgamento do alvo.
  - `pa_medida` é *proxy* da idade (OR ajustado ≈ 1).
  - Metade do efeito da FC é efeito da idade.
  - Alvo com 57,7% × 42,3%, sem necessidade de reamostragem.

## Fase 5 — Slides e arguição
- Deck de **~13 slides para 15 minutos**, numerados, padronizados, com pouco texto e figuras legíveis. Gere em PPTX, com notas do apresentador em cada slide (o "porquê" das decisões).
- Crie um arquivo à parte, `perguntas_arguicao.md`, com ~20 perguntas prováveis e respostas curtas. Exemplos: por que limpar por curva do CDC e não pelo IQR? Por que não imputar antes do treino/teste? O que é vazamento e onde aparece aqui? Por que χ² por quartis e também |r|? Por que a PA ausente não indica doença?

## Fase 6 — Organização do repositório
- Atualize o `README.md` com: estrutura de pastas, ordem de execução, dependências, a nota de que precisa de internet para o CDC, e quem fez cada parte.
- **Não faça `git commit`, `git push` nem apague arquivos sem me perguntar.**

# REGRAS DE CONDUTA
1. Não altere o `UCMF_raw.csv` nem o `UCMF_limpo.csv` de referência.
2. Mantenha a lógica de limpeza da Júlia. Mudanças só com justificativa registrada e minha aprovação.
3. Não invente resultado: se algo não rodar ou não bater, diga claramente.
4. Antes de qualquer ação demorada ou destrutiva, resuma o plano e espere meu "ok".
5. Ao terminar cada fase, me entregue um resumo curto do que fez, do que encontrou e das perguntas em aberto.

# ENTREGÁVEIS FINAIS
- Notebook executado e `UCMF_limpo.csv` validado.
- `relatorio_A1.docx` e `relatorio_A1.pdf` (≤ 5 páginas, confirmado).
- `apresentacao_A1.pptx`.
- `perguntas_arguicao.md`.
- `README.md` atualizado.
- Um `RESUMO_DAS_ALTERACOES.md` listando tudo o que foi mudado e por quê.



mostre tudo em portugues
