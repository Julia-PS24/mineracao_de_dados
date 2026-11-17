"""Pré-processamento da base UCMF para a Avaliação A2.

Este módulo junta as duas modelagens feitas pelo grupo:

- a classe `PreprocessadorUCMF` é a da Parte 6 da A1 ("Análise Bivariada/analise_bivariada.ipynb"),
  reescrita como transformador do scikit-learn (`fit`/`transform`) para entrar num `Pipeline` e ser
  reajustada DENTRO de cada dobra da validação cruzada. Sem isso, medianas, médias, desvios e
  categorias frequentes aprendidos na base inteira vazariam para as dobras de validação;
- o parâmetro `excluir_grupos` retira grupos inteiros de colunas, o que permite medir um cenário
  contra o outro sem duplicar código.

Duas correções em relação à A1, decididas pelo grupo em 16/11/2026:

1. **A coluna `grupo_paciente` não é usada.** A chave da A1 (data de atendimento + data de
   nascimento) não identifica paciente: dos 160 grupos com mais de uma linha, 31 reúnem registros de
   sexos diferentes e 42 reúnem laudos diferentes - são crianças distintas atendidas no mesmo dia.
   A divisão e as dobras passam a ser `StratifiedKFold` (estratificadas pelo alvo, sem agrupamento),
   e cada linha é tratada como uma consulta independente. `verificar_grupo_paciente` reproduz a
   evidência.
2. **O vazamento excluído é o grupo `achados_exame_fisico` inteiro** (SOPRO, B2 e PULSOS), e não
   apenas o SOPRO: os três são anotados no mesmo exame que produz o rótulo Normal/Anormal. O motivo
   do encaminhamento é mantido, porque é escrito por outro médico antes da consulta.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedKFold
from sklearn.utils.validation import check_is_fitted

# ---------------------------------------------------------------- constantes
RANDOM_STATE = 42
ALVO = 'NORMAL X ANORMAL'
CLASSE_POSITIVA = 'Anormal'
N_MIN = 30                                   # categoria/coluna com menos casos é agrupada como rara
FAIXAS_IDADE = [0, 1, 5, 10, 15, 19]         # mesmas faixas da limpeza e da bivariada
ROTULOS_FAIXAS = ['0–1', '1–5', '5–10', '10–15', '15–19']

N_DOBRAS = 5                                 # 5 dobras: a 1ª é o teste (80/20), as outras validam

# Cenários de atributos. A exclusão é por grupo temático (ver `grupo_da_coluna`).
TODOS = ()                                                        # 47 colunas - régua do vazamento
VAZAMENTO = ('achados_exame_fisico',)                             # 37 colunas - cenário principal
SEM_MOTIVO = ('achados_exame_fisico', 'motivo_consulta')          # 19 colunas - triagem estrita

CENARIOS = {
    'Com exame físico (47)': TODOS,
    'Sem exame físico (37)': VAZAMENTO,
    'Sem exame físico e sem motivo (19)': SEM_MOTIVO,
}
CENARIO_PRINCIPAL = 'Sem exame físico (37)'


def raiz_projeto(inicio=None):
    """Pasta do projeto: a primeira, subindo a partir de `inicio`, que contém o UCMF_raw.csv."""
    inicio = Path(inicio or Path.cwd()).resolve()
    return next(p for p in (inicio, *inicio.parents) if (p / 'UCMF_raw.csv').exists())


def carregar_base(raiz=None):
    """Lê a base limpa da A1 (10.576 x 51). Devolve (df, y), com y = 1 para Anormal."""
    raiz = Path(raiz) if raiz else raiz_projeto()
    df = pd.read_csv(raiz / 'Limpeza' / 'UCMF_limpo.csv')
    y = (df[ALVO] == CLASSE_POSITIVA).astype(int).rename('alvo')
    return df, y


def dividir_treino_teste(df, y, random_state=RANDOM_STATE):
    """Divisão 80/20 estratificada pelo alvo: a 1ª dobra de um `StratifiedKFold` de 5.

    Não é um corte arbitrário - é uma das cinco partições de uma validação cruzada, o que mantém a
    proporção de Anormais (42,4%) nos dois lados. Sem agrupamento por `grupo_paciente` (ver o
    cabeçalho do módulo). Devolve os índices posicionais de treino e de teste.
    """
    skf = StratifiedKFold(n_splits=N_DOBRAS, shuffle=True, random_state=random_state)
    return next(skf.split(df, y))


def dobras(random_state=RANDOM_STATE):
    """As dobras usadas para escolher hiperparâmetros, modelo e limiar, sempre dentro do treino."""
    return StratifiedKFold(n_splits=N_DOBRAS, shuffle=True, random_state=random_state)


def verificar_grupo_paciente(df):
    """Evidência de que a chave `grupo_paciente` da A1 não identifica paciente.

    Devolve uma tabela com o que foi verificado, usada na seção de metodologia do relatório.
    """
    g = df['grupo_paciente']
    tamanho = g.value_counts()
    multi = tamanho[tamanho > 1]
    sub = df[g.isin(multi.index)]

    def difere(coluna):
        return sum(1 for _, b in sub.groupby('grupo_paciente') if b[coluna].dropna().nunique() > 1)

    linhas = [
        ('consultas na base limpa', len(df)),
        ('valores distintos de grupo_paciente', int(g.nunique())),
        ('grupos com mais de uma consulta', int(len(multi))),
        ('consultas nesses grupos', int(multi.sum())),
        ('maior grupo (consultas)', int(tamanho.max())),
        ('grupos multi-consulta com SEXO diferente', difere('SEXO')),
        ('grupos multi-consulta com laudo diferente', difere(ALVO)),
    ]
    return pd.DataFrame(linhas, columns=['verificação', 'valor'])


def grupo_da_coluna(c):
    """Grupo temático de cada coluna gerada pelo pré-processador (igual ao da A1)."""
    if c.startswith(('SOPRO_', 'B2_')) or c == 'pulsos_alterados':
        return 'achados_exame_fisico'
    if c.startswith('motivo_'):
        return 'motivo_consulta'
    if c.startswith('sint_') or c == 'hda_ausente':
        return 'sintomas'
    if c in ('IDADE_log_z', 'IMC_z'):
        return 'antropometria'
    if c in ('FC_z', 'PAS_z', 'PAD_z', 'PPA_ord', 'pa_medida', 'ppa_calculada'):
        return 'sinais_vitais_e_pressao'
    if c in ('SEXO_M', 'sexo_ausente'):
        return 'demografica'
    return 'outro'


# ------------------------------------------------------------ pré-processador
class PreprocessadorUCMF(TransformerMixin, BaseEstimator):
    """Aplica as transformações da A1 (Tabela 6 do relatório da A1).

    fit(df_treino)  -> aprende medianas, médias, desvios, modas e categorias frequentes só no treino.
    transform(df)   -> aplica o que foi aprendido (treino, validação, teste ou dados novos).

    Parâmetros
    ----------
    min_casos : int
        Colunas binárias e categorias com menos casos que isso no treino são agrupadas.
    excluir_grupos : tuple de str
        Grupos de colunas (ver `grupo_da_coluna`) retirados da saída. O padrão retira os achados do
        exame físico; `()` reproduz exatamente as 47 colunas da A1.
    """

    Z_FAIXA = ['FC', 'PA SISTOLICA', 'PA DIASTOLICA']    # z-score dentro da faixa etária
    Z_GLOBAL = ['IDADE_log', 'IMC']                      # z-score global; IDADE entra como log(1 + idade)
    ORDEM_PPA = {'Normal': 0, 'Pré-hipertensão': 1, 'HAS estágio 1': 2, 'HAS estágio 2': 3}

    def __init__(self, min_casos=N_MIN, excluir_grupos=VAZAMENTO):
        self.min_casos = min_casos
        self.excluir_grupos = excluir_grupos

    def _faixa(self, idade):
        return pd.cut(idade, FAIXAS_IDADE, include_lowest=True, labels=False)

    def _imputar(self, df):
        """Preenche FC, PA e IMC pela mediana da faixa etária (aprendida no treino)."""
        d = df.copy()
        faixa = self._faixa(d['IDADE'])
        for c in self.Z_FAIXA + ['IMC']:
            med = faixa.map(self.mediana_faixa_[c]).astype(float)
            d[c] = d[c].fillna(med).fillna(self.mediana_global_[c])
        d['IDADE_log'] = np.log1p(d['IDADE'])
        return d

    def fit(self, X, y=None):
        df = X
        faixa = self._faixa(df['IDADE'])
        cols_med = self.Z_FAIXA + ['IMC']
        self.mediana_faixa_ = {c: df[c].groupby(faixa).median() for c in cols_med}
        self.mediana_global_ = {c: df[c].median() for c in cols_med}
        d = self._imputar(df)
        self.media_faixa_ = {c: d[c].groupby(faixa).mean() for c in self.Z_FAIXA}
        self.dp_faixa_ = {c: d[c].groupby(faixa).std() for c in self.Z_FAIXA}
        self.media_glob_ = {c: d[c].mean() for c in self.Z_GLOBAL}
        self.dp_glob_ = {c: d[c].std() for c in self.Z_GLOBAL}
        self.moda_ = {c: df[c].mode().iloc[0] for c in ['SEXO', 'SOPRO', 'B2', 'PULSOS']}
        self.cat_freq_ = {c: [k for k, n in df[c].fillna(self.moda_[c]).value_counts().items()
                              if n >= self.min_casos]
                          for c in ['SOPRO', 'B2']}
        self.cat_raras_ = {c: sorted(set(df[c].dropna()) - set(self.cat_freq_[c])) for c in ['SOPRO', 'B2']}
        self.bin_cols_ = [c for c in df if c.startswith('sint_') or c.startswith('motivo_')]
        self.bin_raras_ = [c for c in self.bin_cols_ if df[c].sum() < self.min_casos]
        self.feature_names_out_ = list(self._transformar(df.head(1)).columns)
        return self

    def _transformar(self, df):
        d = self._imputar(df)
        faixa = self._faixa(d['IDADE'])
        X = pd.DataFrame(index=df.index)
        # numéricas: z-score global (IDADE, IMC) e z-score por faixa etária (FC, PAS, PAD)
        for c in self.Z_GLOBAL:
            X[f'{c}_z'] = (d[c] - self.media_glob_[c]) / self.dp_glob_[c]
        for c, nome in [('FC', 'FC_z'), ('PA SISTOLICA', 'PAS_z'), ('PA DIASTOLICA', 'PAD_z')]:
            X[nome] = (d[c] - faixa.map(self.media_faixa_[c])) / faixa.map(self.dp_faixa_[c])
        # pressão: indicador + PPA ordinal (sem PA = 0, distinguido pelo indicador)
        X['pa_medida'] = df['pa_medida'].astype(int)
        X['PPA_ord'] = df['PPA_calc'].map(self.ORDEM_PPA).fillna(0).astype(int)
        X['ppa_calculada'] = df['PPA_calc'].notna().astype(int)
        # binárias e one-hot
        X['SEXO_M'] = (df['SEXO'].fillna(self.moda_['SEXO']) == 'M').astype(int)
        X['sexo_ausente'] = df['SEXO'].isna().astype(int)
        X['pulsos_alterados'] = (df['PULSOS'].fillna(self.moda_['PULSOS']) != 'Normais').astype(int)
        for c in ['SOPRO', 'B2']:
            v = df[c].fillna(self.moda_[c])
            for cat in self.cat_freq_[c]:
                X[f'{c}_{cat}'] = (v == cat).astype(int)
            if self.cat_raras_[c]:
                X[f'{c}_raras'] = (~v.isin(self.cat_freq_[c])).astype(int)
        # sintomas e motivos (já são 0/1); colunas raras viram uma só
        ok = [c for c in self.bin_cols_ if c not in self.bin_raras_]
        X[ok] = df[ok].astype(int)
        X['motivo_raro'] = df[self.bin_raras_].max(axis=1).astype(int) if self.bin_raras_ else 0
        X[['hda_ausente', 'motivo_ausente']] = df[['hda_ausente', 'motivo_ausente']].astype(int)
        # exclusão dos grupos com vazamento
        excluir = [c for c in X if grupo_da_coluna(c) in self.excluir_grupos]
        return X.drop(columns=excluir)

    def transform(self, X):
        check_is_fitted(self, 'feature_names_out_')
        return self._transformar(X)[self.feature_names_out_]

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, 'feature_names_out_')
        return np.asarray(self.feature_names_out_, dtype=object)
