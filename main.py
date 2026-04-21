from augmentor import create_random_variation

schema = {
    "tables": [
        {
            "name": "escola",
            "columns": [
                {"name": "id_escola", "description": "ID da Escola", "type": "string"},
                {"name": "ano", "description": "Ano de referência para a linha atual", "type": "number", "min": 2009, "max": 2024},
                {"name": "internet", "description": "A escola possui acesso à internet?", "type": "binary"},
                {"name": "quantidade_computador", "description": "Quantidade de computadores na escola", "type": "number", "min": 0, "max": 1000, "semantic_group": "quantidade_item"},
                {"name": "quantidade_tablet_aluno", "description": "Quantidade de tablet em uso pelos alunos", "type": "number", "min": 0, "max": 1000, "semantic_group": "quantidade_item"},
                {"name": "quantidade_desktop_aluno", "description": "Quantidade de computador de mesa (desktop) em uso pelos alunos", "type": "number", "min": 0, "max": 1000, "semantic_group": "quantidade_item"},
                {"name": "quantidade_equipamento_foto", "description": "Quantidade de equipamentos de fotografia na escola", "type": "number", "min": 0, "max": 1000, "semantic_group": "quantidade_item"},
                {"name": "quantidade_matricula_educacao_basica", "description": "Quantidade de matrículas no ensino básico", "type": "number", "min": 0, "max": 4000, "semantic_group": "quantidade_matricula"},
                {"name": "quantidade_matricula_fundamental", "description": "Quantidade de matrículas no ensino fundamental", "type": "number", "min": 0, "max": 4000, "semantic_group": "quantidade_matricula"},
                {"name": "quantidade_matricula_medio", "description": "Quantidade de matrículas no ensino médio", "type": "number", "min": 0, "max": 4000, "semantic_group": "quantidade_matricula"},
                {
                    "name": "sigla_uf",
                    "description": "Sigla da Unidade da Federação",
                    "type": "enum",
                    "value_group_labels": {
                        "nordeste": "Nordeste",
                        "sul": "Sul",
                        "sudeste": "Sudeste",
                        "norte": "Norte",
                        "centro_oeste": "Centro-Oeste",
                    },
                    "enums": [
                        {"value": "AC", "description": "Acre", "value_group": "norte"},
                        {"value": "AL", "description": "Alagoas", "value_group": "nordeste"},
                        {"value": "AP", "description": "Amapá", "value_group": "norte"},
                        {"value": "AM", "description": "Amazonas", "value_group": "norte"},
                        {"value": "BA", "description": "Bahia", "value_group": "nordeste"},
                        {"value": "CE", "description": "Ceará", "value_group": "nordeste"},
                        {"value": "DF", "description": "Distrito Federal", "value_group": "centro_oeste"},
                        {"value": "ES", "description": "Espírito Santo", "value_group": "sudeste"},
                        {"value": "GO", "description": "Goiás", "value_group": "centro_oeste"},
                        {"value": "MA", "description": "Maranhão", "value_group": "nordeste"},
                        {"value": "MT", "description": "Mato Grosso", "value_group": "centro_oeste"},
                        {"value": "MS", "description": "Mato Grosso do Sul", "value_group": "centro_oeste"},
                        {"value": "MG", "description": "Minas Gerais", "value_group": "sudeste"},
                        {"value": "PA", "description": "Pará", "value_group": "norte"},
                        {"value": "PB", "description": "Paraíba", "value_group": "nordeste"},
                        {"value": "PR", "description": "Paraná", "value_group": "sul"},
                        {"value": "PE", "description": "Pernambuco", "value_group": "nordeste"},
                        {"value": "PI", "description": "Piauí", "value_group": "nordeste"},
                        {"value": "RJ", "description": "Rio de Janeiro", "value_group": "sudeste"},
                        {"value": "RN", "description": "Rio Grande do Norte", "value_group": "nordeste"},
                        {"value": "RS", "description": "Rio Grande do Sul", "value_group": "sul"},
                        {"value": "RO", "description": "Rondônia", "value_group": "norte"},
                        {"value": "RR", "description": "Roraima", "value_group": "norte"},
                        {"value": "SC", "description": "Santa Catarina", "value_group": "sul"},
                        {"value": "SP", "description": "São Paulo", "value_group": "sudeste"},
                        {"value": "SE", "description": "Sergipe", "value_group": "nordeste"},
                        {"value": "TO", "description": "Tocantins", "value_group": "norte"},
                    ],
                },
            ],
        },
        {
            "name": "matricula",
            "columns": [
                {"name": "id_matricula", "description": "ID da Escola", "type": "string"},
                {"name": "ano", "description": "Ano de referência para a linha atual", "type": "number", "min": 2009, "max": 2024},
                {
                    "name": "sigla_uf",
                    "description": "Sigla da Unidade da Federação",
                    "type": "enum",
                    "value_group_labels": {
                        "nordeste": "Nordeste",
                        "sul": "Sul",
                        "sudeste": "Sudeste",
                        "norte": "Norte",
                        "centro_oeste": "Centro-Oeste",
                    },
                    "enums": [
                        {"value": "AC", "description": "Acre", "value_group": "norte"},
                        {"value": "AL", "description": "Alagoas", "value_group": "nordeste"},
                        {"value": "AP", "description": "Amapá", "value_group": "norte"},
                        {"value": "AM", "description": "Amazonas", "value_group": "norte"},
                        {"value": "BA", "description": "Bahia", "value_group": "nordeste"},
                        {"value": "CE", "description": "Ceará", "value_group": "nordeste"},
                        {"value": "DF", "description": "Distrito Federal", "value_group": "centro_oeste"},
                        {"value": "ES", "description": "Espírito Santo", "value_group": "sudeste"},
                        {"value": "GO", "description": "Goiás", "value_group": "centro_oeste"},
                        {"value": "MA", "description": "Maranhão", "value_group": "nordeste"},
                        {"value": "MT", "description": "Mato Grosso", "value_group": "centro_oeste"},
                        {"value": "MS", "description": "Mato Grosso do Sul", "value_group": "centro_oeste"},
                        {"value": "MG", "description": "Minas Gerais", "value_group": "sudeste"},
                        {"value": "PA", "description": "Pará", "value_group": "norte"},
                        {"value": "PB", "description": "Paraíba", "value_group": "nordeste"},
                        {"value": "PR", "description": "Paraná", "value_group": "sul"},
                        {"value": "PE", "description": "Pernambuco", "value_group": "nordeste"},
                        {"value": "PI", "description": "Piauí", "value_group": "nordeste"},
                        {"value": "RJ", "description": "Rio de Janeiro", "value_group": "sudeste"},
                        {"value": "RN", "description": "Rio Grande do Norte", "value_group": "nordeste"},
                        {"value": "RS", "description": "Rio Grande do Sul", "value_group": "sul"},
                        {"value": "RO", "description": "Rondônia", "value_group": "norte"},
                        {"value": "RR", "description": "Roraima", "value_group": "norte"},
                        {"value": "SC", "description": "Santa Catarina", "value_group": "sul"},
                        {"value": "SP", "description": "São Paulo", "value_group": "sudeste"},
                        {"value": "SE", "description": "Sergipe", "value_group": "nordeste"},
                        {"value": "TO", "description": "Tocantins", "value_group": "norte"},
                    ],
                },
            ],
        },
    ]
}

original_sqls = [
    """
SELECT
    m.ano,
    COUNT(DISTINCT m.id_matricula) AS total_alunos
FROM matricula m
JOIN escola e ON m.id_escola = e.id_escola AND m.ano = e.ano
WHERE m.ano >= (SELECT MAX(ano) FROM matricula) - 2
  AND e.sigla_uf IN ('AC','AP','AM','PA','RO','RR','TO')
  AND e.internet = 0
GROUP BY m.ano
ORDER BY m.ano;
    """
]

original_querys = [
    "Nos últimos 3 anos, quantos alunos estão matriculados em escolas da região Norte que não possuem internet?"
]

if __name__ == "__main__":
    for i in range(len(original_querys)):
        print(" = = = = = = = = = = = = = = = =")
        original_query = original_querys[i]
        original_sql = original_sqls[i]
        (new_query, new_sql) = create_random_variation(schema, original_query, original_sql)

        print("============= ORIGINAL ================")
        print("Pergunta original:", original_query)
        print("SQL original:\n")
        print(original_sql)
        print("========== MODIFICADO ===============")
        print("Pergunta modificada:", new_query)
        print("Novo SQL:\n")
        print(new_sql)
