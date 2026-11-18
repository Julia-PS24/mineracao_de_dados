# A2 — decisões de metodologia e modelagem

Registro das decisões tomadas pelo grupo em 16/11/2026, com a justificativa de cada uma e onde
checar o número. Este arquivo é a origem do que o relatório afirma na Seção III (Metodologia) e na
declaração de uso de IA (Seção VI).

Todos os números estão em `Modelagem_A2/tabelas/`, e a base do relatório é **gerada a partir
deles** por `Modelagem_A2/gerar_relatorio_A2.py`. A versão final (`relatorio_A2_revisado`) foi
revisada pelo grupo sobre essa base.

---

## 1. Qual atributo sai por vazamento

**Decisão: saem os três achados do exame físico — SOPRO, B2 e PULSOS (10 colunas codificadas).
O motivo do encaminhamento fica.**

O enunciado pede excluir "o atributo que indique data leakage", no singular. A A1 havia apontado
quatro grupos de risco. O grupo optou pelo critério de **origem da informação**: sopro, segunda
bulha e pulsos são anotados no mesmo exame que produz o laudo, logo nenhum deles está disponível
numa triagem. Excluir só o sopro deixaria vazamento residual.

| Cenário | Atributos | AUC (val. cruzada) | AUC (teste) |
|---|---|---|---|
| Com o exame físico | 47 | 0,950 | 0,956 |
| **Sem o exame físico** | **37** | **0,777** | **0,802** |
| Sem exame físico e sem motivo | 19 | 0,674 | 0,684 |

O primeiro cenário entra no relatório **só como régua**: a queda de 0,174 mede o vazamento, não
capacidade preditiva. O terceiro entra como análise de sensibilidade.

**Por que o motivo do encaminhamento não é vazamento:** é escrito por outro médico, antes da consulta. E não reproduz o achado do exame — das 2.122 crianças encaminhadas por sopro, o cardiologista confirmou em 1.653 (78%), e nas 469 em que não confirmou só 11,7% têm laudo anormal;
na direção oposta, das 3.994 com sopro no exame, apenas 41% vinham encaminhadas por sopro. É
suspeita prévia: informativa e imperfeita, como se espera de um atributo legítimo.

---

## 2. Protocolo de validação

**Decisão: divisão 80/20 estratificada, com validação cruzada de 5 dobras dentro do treino, mais
validação cruzada aninhada 5×3 como confirmação.**

O que o professor criticou foi o 80/20 **simples e não estratificado**, usado como única evidência.
A versão adotada corrige os três pontos:

- a divisão é estratificada (42,4% de anormais nos dois lados) e é a primeira partição de um
  `StratifiedKFold` de 5 — não um corte solto;
- **nenhuma decisão usa o teste**: hiperparâmetros, escolha do modelo e limiar saem da validação
  cruzada no treino. O teste é aberto uma vez, no fim;
- a aninhada 5×3 sobre as 10.576 consultas confirma o resultado sem depender de corte algum.

A confirmação foi útil: o teste dá 0,802, a validação cruzada do treino dá 0,777 e a aninhada dá
**0,786 ± 0,013**. O relatório adota esse valor intermediário, por usar a base inteira e não
depender de um corte, e explica a diferença — a partição de teste saiu favorável. Reconhecer isso pesa mais a favor do que reportar o número maior.

---

## 3. A coluna `grupo_paciente`

**Decisão: fica de fora, e a correção é assumida no relatório.**

A A1 juntava consultas com a mesma data de atendimento e a mesma data de nascimento, supondo o
mesmo paciente. A verificação mostrou que a suposição não se sustenta: há 10.407 valores distintos
da chave para 10.576 consultas; só 160 grupos têm mais de uma linha e, desses, **31 reúnem sexos
diferentes** e 42 reúnem laudos diferentes.

Sem agrupamento, a divisão passa a ser `StratifiedKFold`, e o custo está medido: apenas 53 dos
10.407 grupos caem dos dois lados (0,5%). A impossibilidade de identificar consultas repetidas
consta como limitação do estudo.

---

## 4. Algoritmos

**Decisão: mantidos os quatro.**

| Algoritmo | Papel | AUC (val. cruzada, 37 atributos) |
|---|---|---|
| Classe majoritária | piso trivial, não é um modelo | 0,500 |
| Regressão logística | **simples** (o baseline exigido) | 0,764 |
| Floresta aleatória | **complexo** | 0,775 |
| Gradient boosting | **complexo** (o escolhido) | 0,777 |

O gradient boosting foi escolhido por ter a maior AUC **na validação cruzada** — a seleção não pode
olhar o teste. No teste a floresta ficou 0,0007 à frente, diferença que é ruído.

A vantagem dos complexos sobre o baseline é de 0,012, positiva em 98% das reamostragens pareadas
(IC de 0,001 a 0,019). Pequena, mas consistente. Entre floresta e boosting o intervalo inclui o
zero: empate.

---

## 5. Métricas e ponto de operação

**Decisão: mantidas.**

- **Seleção pela AUC**, que não depende do limiar e mede a qualidade da ordenação — o uso
  pretendido numa triagem.
- **Sensibilidade como prioridade clínica:** deixar de sinalizar uma criança é pior que um
  encaminhamento desnecessário.
- **Limiar fixado para sensibilidade 0,80** nas previsões *out-of-fold* do treino (0,30 para o
  boosting) e só então aplicado ao teste, onde deu 0,810. Subir para 0,90 exigiria priorizar 76,9%
  das crianças — a triagem quase deixaria de triar. O relatório trata o ponto de operação como
  decisão clínica, não estatística.
- **Sem reamostragem (SMOTE):** o desbalanceamento é leve (57,6% × 42,4%) e o desequilíbrio entre
  sensibilidade e especificidade é tratado pelo limiar.
- **Importância por permutação**, e também por grupo temático, porque as 18 colunas de motivo
  descrevem uma informação só e se compensam quando embaralhadas uma a uma.

---

## 6. Atributos herdados da A1

**Decisão: mantidos em bloco.**

| Decisão da A1 | Evidência | Mantida |
|---|---|---|
| Peso e altura fora; fica o IMC | ρ com a idade de 0,97 e 0,99 | sim |
| `Convenio` removida | 26,6% ausente, 341 grafias, V de Cramér 0,18 | sim |
| `pa_medida` como indicador | é *proxy* da idade (OR ajustado 1,09), não indica doença | sim, com a ressalva escrita |
| PPA ordinal + 2 indicadores | 76% de PPA nula porque a PA não foi medida | sim |
| Idade como z-score de log(1 + idade) | assimetria cai de 0,76 para −0,25 | sim |
| FC e PA padronizadas dentro da faixa etária | metade do efeito da FC é efeito da idade | sim |

---

## Como funciona cada algoritmo, e por que ele importa aqui

**Classe majoritária — piso, não é um modelo.** Prevê sempre "normal" e não aprende nada. Serve
para mostrar que 0,576 de acurácia se consegue sem modelo nenhum. É ela que desmonta a leitura
ingênua da acurácia.

**Regressão logística — simples.** Calcula uma soma ponderada dos atributos e converte em
probabilidade. Cada atributo ganha um peso fixo, que vira razão de chances: dá para ler "este
atributo multiplica por X a chance de laudo anormal". Supõe efeito linear e aditivo, então não
captura interações sozinha. Importa aqui por dois motivos: é o baseline que o enunciado exige e é
a única que um cardiologista consegue auditar peso a peso.

**Floresta aleatória — complexo.** Treina centenas de árvores, cada uma sobre uma amostra diferente
das linhas e das colunas, e combina os votos. Captura interações sem que ninguém precise
escrevê-las — uma frequência cardíaca alta pesar só em certas faixas de idade, por exemplo.
Importa aqui como teste: se houvesse estrutura não linear relevante que a logística não pega, ela
apareceria.

**Gradient boosting por histogramas — complexo.** Também usa árvores, mas em sequência: cada nova
árvore corrige o erro acumulado das anteriores, em passos pequenos. É hoje o padrão para dados
tabulares como os nossos. Importa aqui porque marca o teto prático do que dá para extrair destes
atributos.

**A conclusão que os quatro juntos permitem.** O melhor modelo complexo ficou 0,012 de AUC acima do
baseline simples, contra 0,174 de diferença entre ter ou não o exame físico — catorze vezes mais.
O limite deste problema não está no algoritmo, está na informação disponível antes do exame. Essa é
a resposta mais forte que temos para a banca.
