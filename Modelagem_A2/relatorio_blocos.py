"""Conteúdo do relatório da A2, independente do formato de saída.

O texto é descrito como uma lista de blocos e renderizado duas vezes (DOCX no layout IEEE e LaTeX
IEEEtran), de modo que as duas versões nunca divirjam. Todos os números vêm das tabelas geradas por
`modelagem_A2.ipynb`: nenhum valor é digitado à mão.

Tipos de bloco: 'resumo', 'chaves', 'h1', 'h2', 'p', 'fig' (nome, legenda, origem) e
'tab' (nome, legenda).
"""

import re
from pathlib import Path

import pandas as pd

TITULO = ('Vazamento de informação na triagem de laudos '
          'cardiológicos pediátricos: o que sobra quando o exame físico sai')
AUTORAS = ['Jamily Vieira', 'Jessyca Rodrigues', 'Júlia Souza', 'Yasmin Mageste']
AFILIACAO = 'Instituto de Informática, Universidade Federal de Goiás'
DISCIPLINA = 'Mineração de Dados — Avaliação A2'
REPOSITORIO = 'https://github.com/Julia-PS24/mineracao_de_dados'
PALAVRAS_CHAVE = ('mineração de dados, classificação, vazamento de informação, '
                  'triagem clínica, cardiologia pediátrica')

CENARIO_PRINCIPAL = 'Sem exame físico (37)'
CENARIO_REGUA = 'Com exame físico (47)'
CENARIO_ESTRITO = 'Sem exame físico e sem motivo (19)'
MODELO_SIMPLES = 'Regressão Logística'


# ------------------------------------------------------------------ utilidades
def v(x, casas=3):
    """Número no padrão brasileiro."""
    return f'{x:.{casas}f}'.replace('.', ',')


def pct(x, casas=1):
    return f'{x:.{casas}f}'.replace('.', ',') + '%'


def milhar(x):
    return f'{int(x):,}'.replace(',', '.')


def _f(x):
    """Converte '0,792' (como sai das tabelas formatadas) em float."""
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.') if ' ' not in x else
                     x.split()[0].replace('.', '').replace(',', '.'))
    return float(x)


class Resultados:
    """Lê as tabelas exportadas pela modelagem e expõe os números usados no texto."""

    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.tab = raiz / 'Modelagem_A2' / 'tabelas'
        self.fig = raiz / 'Modelagem_A2' / 'figuras'
        ler = lambda nome: pd.read_csv(self.tab / f'{nome}.csv')

        self.dados = ler('resumo_dados').set_index('item')['valor']
        self.ver_grupo = ler('verificacao_grupo_paciente').set_index('verificação')['valor']
        self.vazamento = ler('vazamento_exame_fisico').set_index('achado do exame físico')
        self.colunas_grupo = ler('colunas_por_grupo').set_index('grupo de atributos')
        self.hiper = ler('hiperparametros').set_index('modelo')
        self.cv = ler('cv_comparativa').set_index('modelo')
        self.por_dobra = ler('cv_por_dobra')
        self.teste = ler('tabela_comparativa').set_index('modelo')
        self.difs = ler('diferencas_auc').set_index('comparação')
        self.limiares = ler('limiar_oof').set_index('critério')
        self.erros_faixa = ler('erros_por_faixa').set_index('faixa etária')
        self.erros_motivo = ler('erros_por_motivo').set_index('motivo principal')
        self.imp_grupos = ler('importancia_grupos').set_index('grupo')
        self.imp_atr = ler('importancia_atributos').set_index('coluna')
        self.ors = ler('odds_ratios').set_index('coluna')
        self.sopro = ler('sopro_motivo_x_exame')
        self.alvo_faixa = ler('alvo_por_faixa').set_index('faixa etária')
        self.alvo_motivo = ler('alvo_por_motivo').set_index('motivo principal')
        self.regua = ler('regua_vazamento').set_index(['cenário', 'modelo'])
        self.deriva = ler('deriva_temporal')
        self.por_ano = ler('anormal_por_ano')
        self.aninhada = ler('vc_aninhada').set_index('modelo')
        self._matriz = ler('matriz_confusao')

        # O modelo principal é o de maior AUC na VALIDAÇÃO CRUZADA do cenário principal: a escolha
        # não pode usar o teste, que só é aberto depois de tudo decidido.
        no_cenario = self.regua.loc[CENARIO_PRINCIPAL, 'AUC validação cruzada']
        self.melhor = no_cenario.idxmax()
        self.melhor_teste = self.regua.loc[CENARIO_PRINCIPAL, 'AUC teste'].idxmax()

    # ---- atalhos -----------------------------------------------------------
    def auc(self, cenario, modelo=None, onde='AUC validação cruzada'):
        return float(self.regua.loc[(cenario, modelo or self.melhor), onde])

    def t(self, metrica, modelo=None):
        """Métrica do teste, da tabela comparativa."""
        return _f(self.teste.loc[modelo or self.melhor, metrica])

    def sd_cv(self, modelo=None):
        sel = self.por_dobra[self.por_dobra['modelo'] == (modelo or self.melhor)]
        return float(sel['AUC'].std())

    @property
    def confusao(self):
        """(verdadeiro negativo, falso positivo, falso negativo, verdadeiro positivo)."""
        c = self._matriz.set_index(self._matriz.columns[0])
        inteiro = lambda s: int(re.match(r'[\d.]+', str(s)).group().replace('.', ''))
        return (inteiro(c.iloc[0, 0]), inteiro(c.iloc[0, 1]),
                inteiro(c.iloc[1, 0]), inteiro(c.iloc[1, 1]))

    @property
    def n_atributos(self):
        return int(self.dados['atributos de entrada dos modelos (sem o exame físico)'])

    @property
    def limiar_escolhido(self):
        return self.t('limiar')


# ------------------------------------------------------------------- conteúdo
def blocos(r: Resultados):
    """Lista de blocos do artigo, na ordem em que aparecem."""
    saida = []
    A = saida.append

    # --- números usados em mais de um lugar
    n = int(r.dados['consultas na base limpa (A1)'].replace('.', ''))
    n_bruto = int(r.dados['consultas na base bruta'].replace('.', ''))
    pct_anormal = _f(r.dados['exames anormais na base limpa'].split('(')[1].rstrip('%)'))
    n_anormal = int(r.dados['exames anormais na base limpa'].split(' ')[0].replace('.', ''))
    n_treino, n_teste = (int(x.strip().replace('.', ''))
                         for x in r.dados['consultas de treino / teste'].split('/'))
    n_fora = int(r.colunas_grupo.loc['total', 'A1 (todas)']) - r.n_atributos

    auc_regua = r.auc(CENARIO_REGUA)
    auc_princ = r.auc(CENARIO_PRINCIPAL)
    auc_estrito = r.auc(CENARIO_ESTRITO)
    auc_simples = r.auc(CENARIO_PRINCIPAL, MODELO_SIMPLES)
    auc_teste = r.auc(CENARIO_PRINCIPAL, onde='AUC teste')
    auc_aninhada = float(r.aninhada.loc[r.melhor, 'AUC média'])
    sd_aninhada = float(r.aninhada.loc[r.melhor, 'desvio entre dobras'])

    vn, fp, fn, vp = r.confusao
    n_normais, n_anormais_teste = vn + fp, fn + vp
    parecer = r.erros_motivo.loc['Parecer cardiológico']
    estabelecida = r.erros_motivo.loc['Cardiopatia já estabelecida']

    # Uma consulta pode ter mais de um achado alterado, então as linhas da tabela não somam: o
    # total com alteração é o complemento de "nenhum achado alterado".
    sem_alteracao = int(r.vazamento.loc['Nenhum achado alterado', 'consultas'])
    alterado = n - sem_alteracao
    pct_sem = float(r.vazamento.loc['Nenhum achado alterado', '% Anormal'])
    pct_sistolico = float(r.vazamento.loc['Sopro sistólico', '% Anormal'])

    imp_motivo = float(r.imp_grupos.loc['Motivo do encaminhamento', f'{r.melhor} (queda média de AUC)'])
    segundo_grupo = (r.imp_grupos[f'{r.melhor} (queda média de AUC)']
                     .drop('Motivo do encaminhamento').idxmax())
    imp_segundo = float(r.imp_grupos.loc[segundo_grupo, f'{r.melhor} (queda média de AUC)'])
    top_atr = r.imp_atr.index[0]
    imp_top = float(r.imp_atr.iloc[0][r.melhor])

    sopro_cruz = r.sopro.set_index(['encaminhado por sopro', 'sopro no exame'])
    enc_sem_sopro = int(sopro_cruz.loc[('sim', 'não'), 'consultas'])
    pct_enc_sem_sopro = float(sopro_cruz.loc[('sim', 'não'), '% Anormal'])
    enc_total = int(r.sopro[r.sopro['encaminhado por sopro'] == 'sim']['consultas'].sum())
    exame_total = int(r.sopro[r.sopro['sopro no exame'] == 'sim']['consultas'].sum())
    confirmados = int(sopro_cruz.loc[('sim', 'sim'), 'consultas'])

    ano_i, ano_f = int(r.por_ano['ano'].iloc[0]), int(r.por_ano['ano'].iloc[-1])
    pct_ano_i, pct_ano_f = float(r.por_ano['pct_anormal'].iloc[0]), float(r.por_ano['pct_anormal'].iloc[-1])
    linha_deriva = r.deriva.iloc[1]
    auc_deriva = float(linha_deriva[r.melhor])
    pct_deriva = float(linha_deriva['% Anormal na validação'])

    # ------------------------------------------------------------------ resumo
    A(('resumo',
       f'Este trabalho avalia se o laudo de uma consulta de cardiologia pediátrica pode ser '
       f'previsto a partir do que se conhece antes do exame especializado, usando {milhar(n)} '
       f'consultas de um ambulatório universitário. A análise exploratória identificou vazamento '
       f'de informação: sopro, segunda bulha e pulsos são registrados no mesmo exame que produz o '
       f'rótulo, e {pct(pct_sistolico, 0)} das consultas com sopro '
       f'sistólico têm laudo anormal. Esses {n_fora} atributos foram excluídos, restando '
       f'{r.n_atributos}. Quatro algoritmos foram comparados em validação cruzada dentro do '
       f'treino, com o pré-processamento reajustado em cada dobra, e avaliados uma única vez num '
       f'teste de {milhar(n_teste)} consultas. A área sob a curva ROC cai de {v(auc_regua, 2)} '
       f'com o exame físico para {v(auc_princ, 2)} sem ele: a diferença mede o vazamento, não '
       f'capacidade preditiva. O motivo do encaminhamento responde por quase toda a capacidade '
       f'restante, e {pct(parecer["Anormais não encontrados"] / fn * 100, 0)} dos laudos anormais '
       f'não detectados vêm de pedidos de rotina, sem suspeita prévia.'))
    A(('chaves', PALAVRAS_CHAVE))

    # -------------------------------------------------------------- introdução
    A(('h1', 'Introdução'))
    A(('p',
       'Serviços públicos de cardiologia pediátrica recebem mais encaminhamentos do que conseguem '
       'atender com prontidão. Uma ferramenta capaz de ordenar a fila pela probabilidade de laudo '
       'alterado teria valor prático: adiantaria a avaliação das crianças com maior risco sem '
       'exigir recursos adicionais. A pergunta deste trabalho é se essa ordenação é possível com '
       'a informação que existe *antes* da consulta especializada.'))
    A(('p',
       f'A base utilizada reúne {milhar(n_bruto)} consultas de um ambulatório universitário, '
       f'reduzidas a {milhar(n)} após a limpeza realizada na etapa anterior do estudo, das quais '
       f'{milhar(n_anormal)} ({pct(pct_anormal)}) têm laudo anormal. A tarefa de mineração é a '
       f'classificação binária desse desfecho.'))
    A(('p',
       'A principal dificuldade não é o algoritmo, e sim decidir quais atributos podem ser usados. '
       'Vários deles descrevem o próprio exame cujo resultado se quer prever, e um modelo que os '
       'utilize alcança desempenho elevado sem ter utilidade alguma: prevê o laudo com o laudo. '
       'O vazamento de informação é um erro de formulação que a validação cruzada não detecta, '
       'porque não decorre de sobreajuste [8]. Este relatório identifica os atributos nessa '
       'condição, exclui-os, mede quanto o desempenho cai com a exclusão e examina o que resta.'))
    A(('p',
       f'Todo o código, com semente aleatória fixa, está no repositório indicado na primeira '
       f'página, implementado em Python com scikit-learn [1], pandas [2] e matplotlib [3]. Quatro '
       f'algoritmos foram comparados: um piso trivial, um modelo linear interpretável e dois '
       f'conjuntos de árvores de decisão.'))

    # ------------------------------------------------------------------- dados
    A(('h1', 'Dados e Análise Exploratória'))
    A(('p',
       f'Cada linha da base corresponde a uma consulta e reúne dados demográficos (idade e sexo), '
       f'medidas antropométricas (peso, altura e índice de massa corporal), sinais vitais '
       f'(frequência cardíaca e pressão arterial), sintomas relatados, o motivo do encaminhamento '
       f'e os achados do exame físico realizado pelo cardiologista. O alvo é o laudo final, '
       f'normal ou anormal. O desbalanceamento é leve — {pct(pct_anormal)} de laudos anormais '
       f'contra {pct(100 - pct_anormal)} de normais — e não justifica reamostragem; justifica, '
       f'porém, não interpretar a acurácia isoladamente, já que prever sempre "normal" alcança '
       f'{v(1 - pct_anormal / 100, 3)}.'))
    A(('h2', 'O atributo com vazamento de informação'))
    A(('p',
       f'O rótulo é a conclusão do cardiologista após o exame. Sopro, segunda bulha e pulsos são '
       f'exatamente o que ele ausculta e palpa nesse mesmo exame, e por isso não estão disponíveis '
       f'no momento em que uma triagem precisaria da previsão. A Fig. {{fig:fig1_vazamento_exame_fisico}} mostra a dimensão do '
       f'problema: entre as {milhar(alterado)} consultas com algum achado alterado, a proporção de '
       f'laudos anormais chega a {pct(pct_sistolico, 0)} no sopro sistólico, enquanto as '
       f'{milhar(sem_alteracao)} consultas sem nenhuma alteração ficam em {pct(pct_sem)}. '
       f'A etapa anterior do estudo havia medido para o sopro um V de Cramér de 0,84, valor que '
       f'nenhum atributo anterior à consulta alcança.'))
    A(('p',
       f'Os {n_fora} atributos codificados a partir desses três achados foram excluídos da '
       f'análise. O critério é a origem da informação, não a força da associação: pulsos e segunda '
       f'bulha alteram-se em poucas consultas, mas são anotados no mesmo ato clínico e sairiam '
       f'pelo mesmo motivo. Restam {r.n_atributos} atributos de entrada.'))
    A(('p',
       f'O motivo do encaminhamento foi mantido, e essa decisão merece justificativa, já que o '
       f'encaminhamento por sopro é o atributo mais importante dos modelos. Ele é escrito pelo '
       f'médico que encaminha, antes da consulta, e portanto está disponível na triagem. Além '
       f'disso, não reproduz o achado do exame: das {milhar(enc_total)} crianças encaminhadas por '
       f'sopro, o cardiologista o confirmou em {milhar(confirmados)} '
       f'({pct(confirmados / enc_total * 100, 0)}), e as {milhar(enc_sem_sopro)} em que não '
       f'confirmou têm apenas {pct(pct_enc_sem_sopro)} de laudos anormais; na direção oposta, das '
       f'{milhar(exame_total)} consultas com sopro no exame, somente '
       f'{pct(confirmados / exame_total * 100, 0)} vinham encaminhadas por sopro. A suspeita '
       f'prévia é informativa e imperfeita — o que se espera de um atributo legítimo.'))
    A(('fig', 'fig1_vazamento_exame_fisico',
       'Proporção de laudos anormais em cada achado do exame físico, na base limpa. A linha '
       'tracejada marca a proporção do conjunto completo. Achados registrados no mesmo exame que '
       'produz o rótulo separam as classes quase perfeitamente, sinal de vazamento de informação.',
       'A2'))
    A(('p',
       f'Entre os atributos efetivamente utilizáveis, dois se destacam (Fig. {{fig:fig2_alvo_idade_motivo}}). A idade concentra '
       f'o risco: a proporção de laudos anormais cai de '
       f'{pct(float(r.alvo_faixa["pct_anormal"].iloc[0]))} no primeiro ano de vida para '
       f'{pct(float(r.alvo_faixa["pct_anormal"].iloc[-1]))} entre 15 e 19 anos. O motivo do '
       f'encaminhamento separa ainda mais: as consultas por cardiopatia já estabelecida chegam a '
       f'{pct(float(r.alvo_motivo.loc["Cardiopatia já estabelecida", "pct_anormal"]))} de laudos '
       f'anormais, contra '
       f'{pct(float(r.alvo_motivo.loc["Parecer cardiológico", "pct_anormal"]))} nos pedidos de '
       f'parecer cardiológico, que são o motivo mais frequente da base '
       f'({milhar(int(r.alvo_motivo.loc["Parecer cardiológico", "consultas"]))} consultas).'))
    A(('fig', 'fig2_alvo_idade_motivo',
       'Proporção de laudos anormais por faixa etária (a) e por motivo principal do encaminhamento '
       '(b), na base limpa, com o número de consultas entre parênteses. São as duas informações '
       'anteriores à consulta que mais pesam nos modelos.',
       'A2'))

    # -------------------------------------------------------------- metodologia
    A(('h1', 'Metodologia'))
    A(('h2', 'Pré-processamento'))
    A(('p',
       'O pré-processamento herdado da etapa anterior compreende: imputação de frequência cardíaca, '
       'pressão arterial e índice de massa corporal pela mediana da faixa etária; padronização '
       'desses sinais vitais dentro da faixa etária, para separar o efeito da variável do efeito '
       'da idade; transformação logarítmica da idade antes da padronização, o que reduz a '
       'assimetria de 0,76 para −0,25; exclusão de peso e altura, redundantes com a idade '
       '(correlação de Spearman de 0,97 e 0,99); codificação da pressão arterial percentilar, '
       'classificada segundo o Fourth Report [5], como variável ordinal acompanhada de dois '
       'indicadores de ausência; e agrupamento de categorias com menos de 30 casos. O índice de '
       'massa corporal segue as curvas de crescimento do CDC [4], e a faixa etária considerada vai '
       'de 0 a 19 anos, limite usual da pediatria [6].'))
    A(('p',
       'O ponto metodologicamente relevante é *quando* esse ajuste acontece. Medianas, médias, '
       'desvios-padrão, modas e a lista de categorias frequentes são estatísticas aprendidas dos '
       'dados; calculá-las sobre a base inteira antes de separar treino e validação transfere '
       'informação de um conjunto para o outro. Para evitá-lo, o pré-processador foi implementado '
       'como transformador do scikit-learn [1] e colocado em um *pipeline*, de modo que é '
       'reajustado dentro de cada dobra, usando somente as linhas de ajuste daquela dobra.'))
    A(('h2', 'Protocolo de validação'))
    A(('p',
       f'A base foi dividida em {milhar(n_treino)} consultas de treino e {milhar(n_teste)} de '
       f'teste ({pct(pct_anormal)} de laudos anormais em ambos), tomando uma das cinco partições '
       f'de uma divisão estratificada — e não um corte aleatório isolado. Todas as decisões '
       f'(hiperparâmetros, escolha do modelo e limiar de decisão) foram tomadas por validação '
       f'cruzada de cinco dobras estratificadas *dentro do treino*. O teste foi aberto uma única '
       f'vez, após todas as decisões, e nenhum resultado dele realimentou escolha alguma.'))
    A(('p',
       f'A etapa anterior previa agrupar a divisão por uma chave construída a partir da data de '
       f'atendimento e da data de nascimento, supondo identificar o mesmo paciente. A verificação '
       f'realizada aqui não sustenta a suposição: dos '
       f'{int(r.ver_grupo["grupos com mais de uma consulta"])} grupos com mais de uma consulta, '
       f'{int(r.ver_grupo["grupos multi-consulta com SEXO diferente"])} reúnem registros de sexos '
       f'diferentes e {int(r.ver_grupo["grupos multi-consulta com laudo diferente"])} reúnem '
       f'laudos diferentes — são crianças distintas atendidas no mesmo dia. A base não possui '
       f'identificador de paciente, de modo que cada consulta é tratada como observação '
       f'independente, e a impossibilidade de descartar consultas repetidas consta entre as '
       f'limitações do estudo.'))
    A(('p',
       f'Como uma estimativa obtida em um único conjunto de teste depende da partição sorteada, '
       f'o resultado principal foi confirmado por validação cruzada aninhada, com cinco dobras '
       f'externas de avaliação e três internas de escolha de hiperparâmetros, aplicada às '
       f'{milhar(n)} consultas [7]. Nesse protocolo nenhuma observação participa ao mesmo tempo '
       f'da escolha e da avaliação, e a estimativa não depende de um corte específico.'))
    A(('h2', 'Algoritmos e métricas'))
    A(('p',
       f'Quatro algoritmos foram comparados. A classe majoritária fixa o piso: prevê sempre '
       f'"normal" e não aprende nada. A regressão logística é o modelo simples exigido — linear, '
       f'aditivo e auditável coeficiente a coeficiente. A floresta aleatória [9] e o '
       f'*gradient boosting* por histogramas [10] são os modelos complexos, capazes de representar '
       f'efeitos não lineares e interações: a primeira combina centenas de árvores ajustadas a '
       f'amostras distintas, reduzindo variância; o segundo ajusta árvores pequenas em sequência, '
       f'cada uma corrigindo o erro acumulado das anteriores, reduzindo viés. Os hiperparâmetros '
       f'foram escolhidos por busca em grade sobre a área sob a curva ROC média das dobras '
       f'({r.hiper["combinações na grade"].sum()} combinações no total), sempre dentro do treino.'))
    A(('p',
       f'A área sob a curva ROC é a métrica de seleção, por não depender do limiar de decisão e '
       f'medir diretamente a qualidade da ordenação, que é o uso pretendido. Entre as métricas que '
       f'dependem de limiar, a sensibilidade na classe anormal recebe prioridade clínica: deixar '
       f'de sinalizar uma criança com alteração cardíaca é mais grave do que um encaminhamento '
       f'desnecessário. O limiar foi fixado, para cada modelo, no maior valor que alcança '
       f'sensibilidade de {v(0.80, 2)} nas previsões *out-of-fold* do treino, e só então aplicado '
       f'ao teste. A importância dos atributos foi medida por permutação, e não pela redução de '
       f'impureza das árvores, que favorece atributos com muitos valores distintos; a permutação '
       f'foi feita também por grupo temático, porque atributos que descrevem a mesma informação se '
       f'substituem mutuamente quando embaralhados um a um.'))

    # --------------------------------------------------------------- resultados
    A(('h1', 'Resultados e Discussão'))
    A(('tab', 'tabela_comparativa',
       f'Desempenho no cenário com {r.n_atributos} atributos. A coluna de validação cruzada traz a '
       f'média e o desvio-padrão das cinco dobras do treino; as demais referem-se ao conjunto de '
       f'teste ({milhar(n_teste)} consultas), com intervalos de 95% por reamostragem '
       f'*bootstrap*. Sensibilidade, especificidade e F1 usam o limiar fixado no treino.'))
    A(('p',
       f'Os três modelos superam com folga o piso da classe majoritária, e a diferença entre eles '
       f'é pequena (Tabela {{tab:tabela_comparativa}}). Na validação cruzada, que é o critério de seleção, o '
       f'{r.melhor.lower()} alcança {v(auc_princ)} contra {v(auc_simples)} da regressão logística, '
       f'uma vantagem de {v(auc_princ - auc_simples)} com desvio entre dobras de '
       f'{v(r.sd_cv())}. No teste, a reamostragem pareada *bootstrap* [11] — em que os dois modelos são avaliados '
       f'nas mesmas consultas sorteadas — confirma que a vantagem é consistente: a diferença é '
       f'positiva em {pct(float(r.difs.loc[f"{r.melhor} − {MODELO_SIMPLES}", "% das reamostragens > 0"]))} '
       f'das reamostragens. Já a diferença entre os dois modelos complexos é indistinguível de '
       f'zero, com intervalo de {r.difs.loc[f"{r.melhor} − Random Forest", "IC 95%"]}.'))
    A(('p',
       f'A estimativa do teste ({v(auc_teste)}) é mais otimista que a da validação cruzada '
       f'({v(auc_princ)}), o que indica uma partição favorável, não ganho real. A validação '
       f'cruzada aninhada sobre as {milhar(n)} consultas, que não depende de um corte único, '
       f'devolve {v(auc_aninhada)} ± {v(sd_aninhada)} — valor intermediário e o mais conservador '
       f'dos três. É esse o número que o trabalho adota como desempenho esperado.'))
    A(('fig', 'fig4_roc_teste',
       'Curvas ROC no conjunto de teste. A diagonal corresponde ao desempenho de um sorteio. '
       'O ponto destacado marca o limiar fixado no treino para o modelo escolhido. As três curvas '
       'praticamente se sobrepõem: a vantagem dos modelos complexos não se concentra em nenhuma '
       'faixa de limiar.',
       'A2'))
    A(('h2', 'O custo de excluir o exame físico'))
    A(('p',
       f'A Fig. {{fig:fig3_regua_vazamento}} responde à pergunta central. Com os achados do exame físico incluídos, a área '
       f'sob a curva ROC do {r.melhor.lower()} é {v(auc_regua)}; sem eles, {v(auc_princ)}. '
       f'A queda de {v(auc_regua - auc_princ)} não mede perda de capacidade preditiva: mede o '
       f'quanto o laudo estava escrito dentro daqueles atributos. Um modelo com {v(auc_regua, 2)} '
       f'de área sob a curva seria reportado como excelente e seria inútil, porque exige, para '
       f'funcionar, justamente a informação que a triagem não tem. Retirar também o motivo do '
       f'encaminhamento reduz o desempenho a {v(auc_estrito)}, o que delimita o que se pode '
       f'esperar usando apenas o que é medido na própria consulta.'))
    A(('fig', 'fig3_regua_vazamento',
       'Área sob a curva ROC na validação cruzada do treino, por conjunto de atributos. '
       'O primeiro grupo de barras inclui os achados do exame físico e serve apenas de régua para '
       'medir o vazamento; o segundo é o cenário adotado; o terceiro remove também o motivo do '
       'encaminhamento.',
       'A2'))
    A(('h2', 'Análise dos erros'))
    A(('p',
       f'No limiar fixado no treino ({v(r.limiar_escolhido, 2)}), o {r.melhor.lower()} encontra '
       f'{milhar(vp)} dos {milhar(n_anormais_teste)} laudos anormais do teste '
       f'({pct(vp / n_anormais_teste * 100)}) e deixa passar {milhar(fn)}; entre os '
       f'{milhar(n_normais)} laudos normais, prioriza {milhar(fp)} '
       f'({pct(fp / n_normais * 100)}) e libera {milhar(vn)}. A assimetria é deliberada: há cerca '
       f'de {v(fp / fn, 1)} falsos alarmes por laudo anormal perdido, consequência de exigir '
       f'sensibilidade alta. A fila priorizada reúne {milhar(vp + fp)} consultas, das quais '
       f'{pct(vp / (vp + fp) * 100)} são anormais; a fila liberada reúne {milhar(vn + fn)}, com '
       f'{pct(fn / (vn + fn) * 100)} de anormais — menos da metade da proporção da base.'))
    A(('tab', 'matriz_confusao',
       f'Matriz de confusão do modelo escolhido no conjunto de teste, no limiar fixado no treino. '
       f'Os percentuais são por linha, isto é, sobre o total de cada classe real.'))
    A(('p',
       f'Exigir mais sensibilidade custa caro, e de forma não linear. Nas previsões '
       f'*out-of-fold* do treino, passar de sensibilidade '
       f'{v(float(r.limiares.loc["sensibilidade >= 0,75", "sensibilidade"]), 2)} para '
       f'{v(float(r.limiares.loc["sensibilidade >= 0,80", "sensibilidade"]), 2)} eleva a fração de '
       f'crianças priorizadas de '
       f'{pct(float(r.limiares.loc["sensibilidade >= 0,75", "% priorizados"]))} para '
       f'{pct(float(r.limiares.loc["sensibilidade >= 0,80", "% priorizados"]))}; alcançar '
       f'{v(float(r.limiares.loc["sensibilidade >= 0,90", "sensibilidade"]), 2)} exigiria '
       f'priorizar {pct(float(r.limiares.loc["sensibilidade >= 0,90", "% priorizados"]))} — a '
       f'triagem quase deixaria de triar. O ponto de operação é, portanto, uma decisão clínica e '
       f'não estatística; o modelo entrega a curva inteira, e o valor adotado aqui é uma '
       f'convenção de trabalho.'))
    A(('p',
       f'Os erros não se distribuem por igual, e é aí que está a parte interessante. Por faixa '
       f'etária (Tabela {{tab:erros_por_faixa}}), a sensibilidade cai de '
       f'{v(float(r.erros_faixa["sensibilidade"].iloc[0]), 2)} no primeiro ano de vida para '
       f'{v(float(r.erros_faixa["sensibilidade"].iloc[-1]), 2)} entre 15 e 19 anos, enquanto a '
       f'especificidade faz o caminho inverso, de '
       f'{v(float(r.erros_faixa["especificidade"].iloc[0]), 2)} para '
       f'{v(float(r.erros_faixa["especificidade"].iloc[-1]), 2)}. O modelo acompanha a prevalência '
       f'de cada faixa: prioriza quase todos os bebês, entre os quais '
       f'{pct(float(r.erros_faixa["% Anormal"].iloc[0]))} têm laudo anormal, e quase ninguém entre '
       f'os adolescentes.'))
    A(('tab', 'erros_por_faixa',
       f'Desempenho do modelo escolhido por faixa etária, no conjunto de teste e no limiar fixado '
       f'no treino. A última coluna traz o número de laudos anormais não detectados em cada faixa.'))
    A(('p',
       f'Mais revelador, porém, é o motivo do encaminhamento. O desempenho acompanha a '
       f'suspeita que vem no encaminhamento (Fig. {{fig:fig6_erros_por_motivo}}): nas {milhar(estabelecida["n"])} consultas '
       f'por cardiopatia já estabelecida, a sensibilidade é de {v(float(estabelecida["sensibilidade"]), 2)}, '
       f'enquanto nas {milhar(parecer["n"])} consultas de parecer cardiológico, que têm apenas '
       f'{pct(float(parecer["% Anormal"]))} de laudos anormais, ela cai para '
       f'{v(float(parecer["sensibilidade"]), 2)}. Essas últimas concentram '
       f'{int(parecer["Anormais não encontrados"])} dos {milhar(fn)} laudos anormais não '
       f'detectados ({pct(parecer["Anormais não encontrados"] / fn * 100, 0)}).'))
    A(('p',
       f'A leitura clínica é direta e constitui o principal achado do trabalho: o modelo funciona '
       f'como um resumo quantitativo do encaminhamento e da idade. Ordena bem quem já chega com '
       f'suspeita e falha justamente onde a suspeita não existe — nos pedidos de rotina, em que a '
       f'alteração só aparece no exame. Uma triagem automatizada desse tipo adiantaria crianças '
       f'que já seriam priorizadas pela leitura do encaminhamento, e acrescentaria pouco onde mais '
       f'se precisaria dela.'))
    A(('fig', 'fig6_erros_por_motivo',
       'Sensibilidade e especificidade do modelo escolhido no conjunto de teste, por motivo '
       'principal do encaminhamento, no limiar fixado no treino. Os rótulos trazem o número de '
       'consultas e a proporção de laudos anormais de cada grupo.',
       'A2'))
    A(('h2', 'Importância dos atributos'))
    A(('p',
       f'A permutação por grupo (Fig. {{fig:fig5_importancia_grupos}}) mostra uma concentração acentuada: embaralhar as 18 '
       f'colunas do motivo do encaminhamento derruba a área sob a curva em {v(imp_motivo)}, '
       f'enquanto nenhum outro grupo passa de {v(imp_segundo)} — o do grupo '
       f'"{segundo_grupo.lower()}". Os três modelos concordam na ordenação, o que indica que ela '
       f'reflete os dados e não a escolha do algoritmo. Individualmente, o atributo mais '
       f'importante é o encaminhamento por sopro ({v(imp_top)}), seguido pela frequência cardíaca '
       f'e pela idade.'))
    A(('p',
       f'Os coeficientes da regressão logística dão a direção dos efeitos. Aumentam a chance de '
       f'laudo anormal os encaminhamentos que já trazem suspeita — sopro '
       f'(razão de chances {v(float(r.ors.loc["motivo_sopro", "odds ratio"]), 2)}), cardiopatia já '
       f'estabelecida ({v(float(r.ors.loc["motivo_cardiopatia_ja_estabelecida", "odds ratio"]), 2)}) '
       f'e cardiopatia congênita '
       f'({v(float(r.ors.loc["motivo_cardiopatia_congenita", "odds ratio"]), 2)}) — e diminuem os '
       f'pedidos de rotina, como parecer cardiológico '
       f'({v(float(r.ors.loc["motivo_parecer_cardiologico", "odds ratio"]), 2)}) e check-up '
       f'({v(float(r.ors.loc["motivo_check_up", "odds ratio"]), 2)}). A pressão arterial, o índice '
       f'de massa corporal e o sexo têm efeito desprezível, confirmando o que a análise bivariada '
       f'da etapa anterior já indicava.'))
    A(('fig', 'fig5_importancia_grupos',
       'Queda na área sob a curva ROC do teste ao embaralhar, em conjunto, as colunas de cada '
       'grupo temático (média de 30 repetições, barras de desvio-padrão). Entre parênteses, o '
       'número de colunas do grupo.',
       'A2'))
    A(('h2', 'Robustez e limitações'))
    A(('p',
       f'A proporção de laudos anormais diminui ao longo da série histórica, de '
       f'{pct(pct_ano_i)} em {ano_i} para {pct(pct_ano_f)} em {ano_f}, o que sugere mudança no '
       f'perfil dos atendimentos. Como a validação cruzada sorteia as dobras ao acaso e mistura '
       f'os anos, o experimento foi repetido com divisão temporal (Tabela {{tab:deriva_temporal}}): treinando nos anos '
       f'iniciais e validando nos finais, a área sob a curva do {r.melhor.lower()} fica em '
       f'{v(auc_deriva)}, contra {v(auc_teste)} no teste sorteado. A capacidade de ordenar '
       f'resiste; o que muda é a prevalência na validação ({pct(pct_deriva)} contra '
       f'{pct(pct_anormal)} na base), o que desloca o ponto de operação e penaliza a precisão.'))
    A(('tab', 'deriva_temporal',
       'Área sob a curva ROC sob dois protocolos: o teste sorteado e uma divisão temporal, que '
       'treina nos anos iniciais da série e valida nos finais. A diferença de prevalência entre os '
       'dois conjuntos de validação explica parte da variação.'))
    A(('p',
       'Três limitações delimitam o alcance destes resultados. A base não possui identificador de '
       'paciente, de modo que consultas repetidas da mesma criança, se existirem, não podem ser '
       'mantidas do mesmo lado da divisão. O perfil dos atendimentos muda ao longo dos anos, e o '
       'desempenho medido vale para a distribuição observada. Por fim, o rótulo é o laudo '
       'registrado por um cardiologista, não um desfecho confirmado por exame complementar: o '
       'modelo aprende a reproduzir um julgamento clínico, com a variabilidade que lhe é própria.'))

    # ---------------------------------------------------------------- conclusão
    A(('h1', 'Conclusão'))
    A(('p',
       f'A exclusão dos achados do exame físico reduziu a área sob a curva ROC de '
       f'{v(auc_regua, 2)} para {v(auc_princ, 2)}, e a validação cruzada aninhada sobre a base '
       f'completa estima {v(auc_aninhada, 3)} para o melhor modelo. Esses dois números, lidos em '
       f'conjunto, são o resultado do trabalho: o desempenho aparentemente excelente do primeiro '
       f'cenário vinha de atributos registrados no mesmo ato clínico que gera o rótulo, e o '
       f'desempenho honesto é moderado.'))
    A(('p',
       f'A diferença entre o melhor modelo complexo e o baseline linear foi de '
       f'{v(auc_princ - auc_simples)} de área sob a curva, enquanto a exclusão do exame físico '
       f'respondeu por {v(auc_regua - auc_princ)} — '
       f'{(auc_regua - auc_princ) / (auc_princ - auc_simples):.0f} vezes mais. O limite deste '
       f'problema está na informação disponível antes da consulta, não na escolha do algoritmo — e '
       f'em uso clínico a regressão logística seria defensável pela interpretabilidade.'))
    A(('p',
       f'Como triagem, a utilidade é parcial e localizada: o modelo ordena bem as crianças que '
       f'chegam com suspeita registrada no encaminhamento e é fraco nos pedidos de rotina, onde '
       f'estão {pct(parecer["Anormais não encontrados"] / fn * 100, 0)} dos laudos anormais que '
       f'ele deixa passar. Como continuidade, três caminhos se destacam: incorporar atributos '
       f'anteriores à consulta que a base não contém, como histórico familiar e dados do '
       f'pré-natal; tratar o texto livre do encaminhamento, hoje reduzido a categorias; e validar '
       f'o modelo em outro serviço, para separar o que é padrão clínico do que é característica '
       f'deste ambulatório.'))

    # ----------------------------------------------------------------------- IA
    A(('h1', 'Uso de Inteligência Artificial Generativa'))
    A(('p',
       'O assistente Claude (Anthropic) foi utilizado em quatro frentes, sempre a partir do '
       'protocolo definido pelo grupo: organização do repositório e da documentação; escrita do '
       'código de modelagem e das figuras; verificação da suposição de agrupamento por paciente '
       'descrita na Seção III-B, que resultou na correção aqui adotada; e redação deste relatório '
       'a partir das tabelas geradas pela execução do código. Nenhum número apresentado foi '
       'produzido pelo assistente: todos são lidos dos arquivos exportados pela execução, e o '
       'relatório é gerado por um programa que os consulta. As decisões metodológicas — quais '
       'atributos excluir, qual protocolo de validação adotar, quais algoritmos comparar e qual '
       'ponto de operação considerar — foram tomadas pelo grupo e estão registradas no '
       'repositório.'))

    return saida


REFERENCIAS = [
    'F. Pedregosa et al., "Scikit-learn: Machine learning in Python", Journal of Machine Learning '
    'Research, vol. 12, pp. 2825–2830, 2011.',
    'The pandas development team, "pandas-dev/pandas: Pandas", Zenodo, 2024. '
    '[Online]. Disponível em: https://doi.org/10.5281/zenodo.3509134',
    'J. D. Hunter, "Matplotlib: A 2D graphics environment", Computing in Science & Engineering, '
    'vol. 9, no. 3, pp. 90–95, 2007.',
    'R. J. Kuczmarski et al., "2000 CDC growth charts for the United States: methods and '
    'development", Vital and Health Statistics, series 11, no. 246, National Center for Health '
    'Statistics, 2002.',
    'National High Blood Pressure Education Program Working Group on High Blood Pressure in '
    'Children and Adolescents, "The fourth report on the diagnosis, evaluation, and treatment of '
    'high blood pressure in children and adolescents", Pediatrics, vol. 114, no. 2, pp. 555–576, '
    '2004.',
    'American Academy of Pediatrics, Council on Child and Adolescent Health, "Age limits of '
    'pediatrics", Pediatrics, vol. 81, no. 5, p. 736, 1988.',
    'S. Varma e R. Simon, "Bias in error estimation when using cross-validation for model '
    'selection", BMC Bioinformatics, vol. 7, no. 91, 2006.',
    'S. Kaufman, S. Rosset e C. Perlich, "Leakage in data mining: formulation, detection, and '
    'avoidance", ACM Transactions on Knowledge Discovery from Data, vol. 6, no. 4, pp. 1–21, 2012.',
    'L. Breiman, "Random forests", Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.',
    'J. H. Friedman, "Greedy function approximation: a gradient boosting machine", The Annals of '
    'Statistics, vol. 29, no. 5, pp. 1189–1232, 2001.',
    'B. Efron e R. J. Tibshirani, An Introduction to the Bootstrap. New York: Chapman & Hall, 1993.',
]
