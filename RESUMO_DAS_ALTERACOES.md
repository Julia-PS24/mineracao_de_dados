# Resumo das alterações — Avaliação A2

Registro do que foi feito na A2, por quê, e o que mudou em relação ao que a A1 havia previsto.
A A1 (limpeza, univariada e bivariada) **não foi alterada**: `UCMF_raw.csv` e
`Limpeza/UCMF_limpo.csv` continuam como estavam.

---

## 1. De duas modelagens para uma

A A2 foi desenvolvida em paralelo por duas integrantes, com decisões diferentes, e depois reunida
numa única versão. As pastas `Modelagem/` (Jamily) e `Modelagem_julia/` (Júlia) são o material
exploratório que deu origem a `Modelagem_A2/`, a pasta final — e podem ser apagadas.

**O que cada versão contribuiu para a final:**

| De `Modelagem_julia/` | De `Modelagem/` |
|---|---|
| Protocolo de validação (divisão 80/20 + validação cruzada no treino, teste aberto uma vez só) | Régua do vazamento: cenários de 47, 37 e 19 atributos medidos lado a lado |
| Pré-processador parametrizado por grupo de colunas (`excluir_grupos`) | Verificação da chave `grupo_paciente`, com a evidência que levou a abandoná-la |
| Limiar orientado a sensibilidade, fixado no treino | Deriva temporal (treino até 2007, validação de 2008 em diante) |
| Importância por grupo, razões de chance e dependência parcial | Validação cruzada aninhada 5×3 como confirmação independente |
| Erros por faixa etária e por motivo do encaminhamento | Gerador do relatório em DOCX/PDF/LaTeX a partir das tabelas |
| Figuras no formato IEEE (600 dpi, largura de coluna) | Conversor do script em notebook |

**Conferência cruzada:** as duas versões mediram, por caminhos independentes, o cenário de 19
atributos. A diferença foi de 0,002 a 0,004 de AUC (0,680 e 0,682 no gradient boosting; 0,657 e
0,661 na logística). Dois pré-processadores escritos separadamente e dois protocolos diferentes
chegando ao mesmo número é a melhor evidência de reprodutibilidade que o trabalho tem.

---

## 2. Correções em relação ao que a A1 previa

### 2.1 `grupo_paciente` não identifica paciente — abandonada

A A1 construiu uma chave juntando a data de atendimento com a data de nascimento e a tratava como
identificador de paciente, com a intenção de agrupar a divisão treino/teste.

**Verificado** (`Modelagem_A2/tabelas/verificacao_grupo_paciente.csv`): a base tem 10.407 valores
distintos da chave para 10.576 consultas. Só 160 grupos têm mais de uma linha e, desses, **31
reúnem registros de sexos diferentes** e 42 reúnem laudos diferentes — são crianças distintas
atendidas no mesmo dia.

**Decisão:** a coluna não é usada, nem como atributo nem para agrupar. Cada consulta é uma
observação independente, e a divisão passa a ser `StratifiedKFold`. O custo está medido: sem
agrupamento, 53 dos 10.407 grupos caem dos dois lados da divisão (0,5%). A impossibilidade de
identificar consultas repetidas consta como limitação no relatório.

### 2.2 Vazamento: saem os três achados do exame físico, não só o sopro

A A1 apontou quatro grupos de risco (SOPRO, B2, PULSOS e `motivo_*`). O enunciado da A2 fala em
"o atributo que indique data leakage", no singular.

**Decisão do grupo:** excluir o grupo `achados_exame_fisico` inteiro — SOPRO, B2 e PULSOS, 10
colunas codificadas. O critério é a **origem da informação**, não a força da associação: B2 e
pulsos alteram-se em poucas consultas, mas são anotados no mesmo ato clínico que produz o laudo.
Excluir só o sopro deixaria vazamento residual.

**O motivo do encaminhamento foi mantido**, e isso está justificado no relatório com números: é
escrito pelo médico que encaminha, antes da consulta, e não reproduz o achado do exame. Das 2.122
crianças encaminhadas por sopro, o cardiologista confirmou em 78%; das 3.994 com sopro no exame, só
41% vinham encaminhadas por sopro. É suspeita prévia — informativa e imperfeita.

### 2.3 Divisão 80/20, estratificada e sem papel nas decisões

O professor criticou a divisão 80/20 **simples e não estratificada**. A versão final mantém o
holdout, mas corrigido em três pontos:

- é estratificado pelo alvo (42,4% de anormais nos dois lados) e tomado como a primeira partição de
  um `StratifiedKFold` de 5, não como um corte solto;
- **nenhuma decisão usa o teste**: hiperparâmetros, escolha do modelo e limiar saem de validação
  cruzada de 5 dobras dentro do treino;
- o resultado é confirmado por **validação cruzada aninhada 5×3** sobre as 10.576 consultas, que
  não depende de corte nenhum.

A confirmação foi informativa: o teste dá 0,802 e a validação cruzada do treino dá 0,777. A
aninhada dá 0,786 ± 0,013 — valor intermediário. O relatório adota o número mais conservador e diz
por quê.

---

## 3. Arquivos novos

```
Modelagem_A2/
├── preprocessamento.py       PreprocessadorUCMF (regras da A1, interface do scikit-learn),
│                             parametrizado por grupo de colunas; divisão e dobras estratificadas
├── modelagem_A2.ipynb        a modelagem inteira, com as saídas gravadas (43 células)
├── relatorio_blocos.py       texto do relatório; todo número é lido das tabelas
├── gerar_relatorio_A2.py     renderiza DOCX (layout IEEE), .tex (IEEEtran) e PDF
├── figuras/                  7 figuras, 600 dpi, na largura final do artigo
└── tabelas/                  28 CSVs com todos os números do relatório
```

Na raiz: `relatorio_A2.docx`, `relatorio_A2.pdf`, `relatorio_A2.tex`, `perguntas_arguicao_A2.md` e
`decisoes_equipe_A2.md`.

## 4. Arquivos alterados

- **`README.md`** — a seção da A2 passou a descrever `Modelagem_A2/`, o protocolo novo e a divisão
  do trabalho entre as duas modelagens; a lista de cuidados foi corrigida nos pontos de
  `grupo_paciente` e de vazamento.
- **`requirements.txt`** — acrescentados `python-docx` e `pypdf` (geração e conferência do PDF).
- **`perguntas_arguicao_A2.md`** — reescrito para o protocolo e os números finais (35 perguntas).

Nada da A1 foi tocado.

---

## 5. Resultados principais

| Cenário | Atributos | AUC (validação cruzada) | AUC (teste) |
|---|---|---|---|
| Com os achados do exame físico | 47 | 0,950 | 0,956 |
| **Sem o exame físico (adotado)** | **37** | **0,777** | **0,802** |
| Sem exame físico e sem motivo | 19 | 0,674 | 0,684 |

- **Vazamento medido:** 0,174 de AUC — o que o exame físico "explicava" por ser o próprio laudo.
- **Desempenho honesto:** 0,786 ± 0,013 (validação cruzada aninhada na base inteira).
- **Modelos complexos × baseline:** 0,012 de vantagem, positiva em 98% das reamostragens pareadas.
  Catorze vezes menor que o efeito da exclusão do exame físico.
- **Onde o modelo erra:** nos pedidos de rotina. Nas consultas de parecer cardiológico a
  sensibilidade cai para 0,48, e ali estão 124 dos 170 laudos anormais não detectados (73%).
- **Deriva temporal:** a proporção de anormais cai de 55,8% (2003) para 28,6% (2010); treinando até
  2007 e validando depois, a AUC vai a 0,764.

---

## 7. Pendente

- **Publicar no GitHub.** O relatório traz no rodapé da primeira página o link para o repositório
  público, e o conteúdo da A2 ainda não foi enviado. Depende de autorização.
- **Apresentação** (`apresentacao_A2.pptx`), para a semana de 18 a 27/11.
- **Apagar `Modelagem/` e `Modelagem_julia/`** depois que a equipe confirmar a versão final.
