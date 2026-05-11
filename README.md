# Augmentação de Dados Orientada por AST

Ferramenta para gerar variações semânticas de consultas SQL e suas descrições em linguagem natural. Usa transformações de Árvore Sintática Abstrata (AST) combinadas com LLM para criar dados de treinamento para modelos de aprendizado de máquina.

**Objetivo principal:** Dada uma consulta SQL original + descrição em linguagem natural + schema, gera variações semânticas controladas com SQL diferente e descrições adaptadas. As mutações devem alterar a intenção da consulta de forma programática, e a camada LLM ajusta a pergunta em linguagem natural para refletir o novo SQL.

## Pré-requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/) - gerenciador de projetos e pacotes

### Instalando uv

Se você não tem `uv` instalado, siga as instruções em [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/).

Nas plataformas mais comuns:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy BypassUser -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Configuração Local

### 1. Clone o repositório

```bash
git clone https://github.com/ioolliver/ast-driven-data-augmentation-algorithm
cd ast-driven-data-augmentation
```

### 2. Configure o ambiente Python

O `uv` usará automaticamente a versão de Python especificada em `.python-version` (3.12). Se você não tem Python 3.12 instalado, o `uv` pode instalá-lo para você:

```bash
# Instala dependências e cria ambiente virtual
uv sync
```

### 3. Ative o ambiente virtual

```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Após ativar, seu prompt deve mostrar `(.venv)` no início.

## Dependências

As dependências estão definidas em `pyproject.toml`:

- **sqlglot** (>= 30.2.1) - Parsing e manipulação de AST para SQL
- **python-dotenv** (>= 1.0.0) - Carregamento de variáveis de ambiente do arquivo `.env`
- **google-genai** - Cliente da API Google Gemini para adaptação de queries com LLM
- **transformers**, **accelerate**, **torch** e **bitsandbytes** - Dependências opcionais para executar o LLM local em Colab/GPU

Para instalar/atualizar dependências:

```bash
uv sync
```

## Executando o Projeto

### Executar o script principal

```bash
python main.py
```

O script irá executar o exemplo incluído que demonstra como gerar uma variação aleatória de uma consulta SQL com sua descrição em linguagem natural.

### Usar como módulo

Importe as funções de mutação em seu próprio código:

```python
from augmentor import create_random_variation
from mutations import mutate_between, mutate_enum, mutate_agg

schema = {
    "tables": [
        {
            "name": "sua_tabela",
            "columns": [
                {"name": "coluna_numero", "type": "number", "min": 0, "max": 100},
                {"name": "coluna_enum", "type": "enum", "enums": [
                    {"value": "A", "description": "Opção A"},
                    {"value": "B", "description": "Opção B"}
                ]}
            ]
        }
    ]
}

sql_original = "SELECT * FROM sua_tabela WHERE coluna_numero BETWEEN 10 AND 50"
descricao = "Buscar registros com coluna numérica entre 10 e 50"

nova_descricao, novo_sql = create_random_variation(schema, descricao, sql_original)
```

## Estrutura do Projeto

```
.
├── main.py                        # Ponto de entrada: schema, queries de teste e loop de execução
├── augmentor.py                   # Orquestrador: create_random_variation
├── llm.py                         # Camada LLM: prompt, chamada Gemini, format_changelog
├── schema_utils.py                # Utilitários de schema: get_col_info, get_table_name
├── mutations/
│   ├── __init__.py                # Re-exporta todas as funções mutate_*
│   ├── between.py                 # Randomiza limites de cláusulas BETWEEN
│   ├── enum_eq.py                 # Troca valor em comparações de igualdade com enum
│   ├── agg.py                     # Alterna funções de agregação (SUM/AVG/MIN/MAX)
│   ├── threshold_shift.py         # Muda operador de inequação e valor numérico
│   ├── equivalent_column.py       # Troca coluna por outra do mesmo grupo semântico
│   ├── value_group.py             # Troca grupo de valores em cláusula IN (ex: Norte → Sudeste)
│   ├── binary.py                  # Inverte valor binário (0 ↔ 1)
│   └── postgis.py                 # Muta funções PostGIS de raio, distância e operações espaciais
├── pyproject.toml                 # Configuração do projeto e dependências
├── uv.lock                        # Lockfile de dependências
├── .python-version                # Versão do Python (3.12)
├── .env.example                   # Template para variáveis de ambiente
├── .gitignore                     # Arquivos ignorados pelo git
├── AGENTS.md                      # Guia arquitetural para agentes de código
└── README.md                      # Este arquivo
```

## Configuração de Secrets (Google Gemini)

O projeto usa a API Google Gemini para adaptar descrições de consultas. Você precisará configurar sua chave de API.

### Usando arquivo `.env` (Recomendado)

1. Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

2. Obtenha sua chave de API em: https://aistudio.google.com/app/apikey

3. Edite o arquivo `.env` e adicione sua chave:

```env
GEMINI_KEY=sua-chave-de-api-aqui
```

4. Pronto! O arquivo será carregado automaticamente quando você executar o projeto.

**Nota:** O arquivo `.env` é automaticamente ignorado pelo git e nunca será commitado, mantendo sua chave segura.

### Usando variáveis de ambiente do sistema

Alternativamente, você pode definir a variável diretamente:

```bash
# Linux/macOS
export GEMINI_KEY="sua-chave-aqui"

# Windows (PowerShell)
$env:GEMINI_KEY="sua-chave-aqui"
```

O projeto verificará primeiro o arquivo `.env` e depois as variáveis de ambiente do sistema.

## Usando LLM Local no Colab

O arquivo `local-llm.py` expõe `send_to_local_llm(prompt)`, que recebe o prompt completo gerado por `llm.py` e retorna apenas o texto da resposta. Para ativar esse caminho em vez da API Gemini, defina:

```env
LOCAL_LLM=true
LOCAL_LLM_MODEL=Qwen/Qwen3.5-4B-Instruct
LOCAL_LLM_4BIT=true
```

Em um Google Colab com GPU T4, instale as dependências de inferência antes de executar o projeto:

```bash
pip install -U transformers accelerate bitsandbytes torch
```

Parâmetros opcionais:

```env
LOCAL_LLM_MAX_NEW_TOKENS=512
LOCAL_LLM_TEMPERATURE=0.2
LOCAL_LLM_TOP_P=0.9
```

O modelo é carregado de forma lazy na primeira chamada e reutilizado nas chamadas seguintes. O modo 4-bit fica ativo por padrão para reduzir uso de VRAM na T4.

## Tipos de Mutações Suportadas

### 1. BETWEEN (`mutations/between.py`)
Randomiza os limites de uma cláusula `BETWEEN` com valores dentro do min/max do schema.

### 2. Enum por igualdade (`mutations/enum_eq.py`)
Troca o valor de uma comparação `coluna = 'valor'` por outro enum disponível no schema.

### 3. Função de agregação (`mutations/agg.py`)
Alterna aleatoriamente entre `SUM`, `AVG`, `MIN` e `MAX`.

### 4. Threshold shift (`mutations/threshold_shift.py`)
Muda o operador de inequação (`>`, `<`, `>=`, `<=`) e o valor numérico comparado.

### 5. Coluna equivalente (`mutations/equivalent_column.py`)
Substitui uma coluna por outra do mesmo `semantic_group` no schema (ex: `quantidade_computador` → `quantidade_tablet_aluno`).

### 6. Grupo de valores IN (`mutations/value_group.py`)
Troca o conjunto de valores em uma cláusula `IN` por outro grupo definido no schema (ex: estados do Norte → estados do Sul).

### 7. Binário (`mutations/binary.py`)
Inverte o valor de uma coluna binária (`0` → `1` ou `1` → `0`).

### 8. PostGIS (`mutations/postgis.py`)
Aplica mutações semânticas em funções PostGIS comuns:

- `ST_Buffer`: altera raios em metros, mantendo valores repetidos coordenados na mesma consulta.
- `ST_DWithin`: altera o limite de distância em metros.
- `ST_Intersection`: troca a operação espacial por `ST_Union` ou `ST_Difference`.
- `ST_Intersects` com dois buffers: reescreve o padrão estrito `ST_Intersects(ST_Buffer(...), ST_Buffer(...))` para `ST_DWithin(...)`.

Quando o schema não informa metadados geográficos, usa valores padrão:

```python
distance_min_m = 100
distance_max_m = 5000
buffer_min_m = 100
buffer_max_m = 3000
```

Metadados opcionais recomendados para colunas de geometria:

```python
{
    "name": "geometry",
    "type": "geometry",
    "description": "Geometria espacial da localização",
    "geometry_type": "POINT",
    "srid": 4674,
    "metric_srid": 31983,
    "spatial_role": "location",
    "distance_min_m": 100,
    "distance_max_m": 5000,
    "buffer_min_m": 100,
    "buffer_max_m": 3000
}
```

O schema atual não precisa ser atualizado para usar as mutações PostGIS, mas esses campos permitem controlar melhor os intervalos de distância e buffer.

## Estendendo com Novas Mutações

Para adicionar um novo tipo de mutação:

1. Crie `mutations/<feature>.py` com a função `mutate_<feature>(node, changelog, schema)`
2. Exporte em `mutations/__init__.py`
3. Importe e chame dentro de `mutate_operators()` em `augmentor.py`
4. Atualize o schema em `main.py` se precisar de novos metadados de coluna

## Referências

- [sqlglot Documentation](https://sqlglot.readthedocs.io/)
- [Google Gemini API](https://ai.google.dev/)
- [uv Documentation](https://docs.astral.sh/uv/)
