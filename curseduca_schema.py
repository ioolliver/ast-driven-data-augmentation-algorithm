curseduca_schema = {
    "tables": [
        {
            "name": "biblioteca",
            "columns": [
                {
                    "name": "cd_bib",
                    "description": "Código da biblioteca",
                    "type": "number"
                },
                {
                    "name": "nm_bib",
                    "description": "Nome da biblioteca",
                    "type": "string"
                },
                {
                    "name": "tipo",
                    "description": "Tipo da biblioteca",
                    "type": "enum",
                    "enums": [
                        { "value": "Comunitária", "description": "Comunitária" },
                        { "value": "Distrital", "description": "Distrital" },
                        { "value": "4", "description": "Estadual" },
                        { "value": "5", "description": "Federal" },
                        { "value": "6", "description": "Municipal" },
                        { "value": "7", "description": "Mista" }
                    ]
                },
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "cd_dist",
                    "description": "Código do distrito",
                    "type": "string"
                },
                {
                    "name": "cd_bairro",
                    "description": "Código do bairro",
                    "type": "string"
                },
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "nm_bairro",
                    "description": "Nome do bairro",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "logradouro",
                    "description": "Logradouro do endereço",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "num",
                    "description": "Número do endereço",
                    "type": "string"
                },
                {
                    "name": "compl",
                    "description": "Complemento do endereço",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "bairro",
                    "description": "Bairro do endereço",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "cep",
                    "description": "CEP do endereço",
                    "type": "string"
                },
                {
                    "name": "telefone",
                    "description": "Telefone para contato",
                    "type": "string", 
                    "semantic_group": "contact_columns"
                },
                {
                    "name": "email",
                    "description": "Endereço de email para contato",
                    "type": "string",
                    "semantic_group": "contact_columns"
                },
                {
                    "name": "latitude",
                    "description": "Coordenada geográfica de latitude",
                    "type": "number",
                    "min": -33.75,
                    "max": 5.27
                },
                {
                    "name": "longitude",
                    "description": "Coordenada geográfica de longitude",
                    "type": "number",
                    "min": -73.99,
                    "max": -34.79
                },
                {
                    "name": "geometry",
                    "type": "geometry",
                    "description": "Geometria espacial da localização da biblioteca",
                    "geometry_type": "POINT",
                    "distance_min_m": 100,
                    "distance_max_m": 2000,
                    "buffer_min_m": 100,
                    "buffer_max_m": 1000
                }
            ]
        },
        {
            "name": "centro_pop",
            "columns": [
                {
                    "name": "nu_identif",
                    "description": "Número de identificação do centro populacional",
                    "type": "number"
                },
                {
                    "name": "q0_1",
                    "description": "Nome do centro populacional",
                    "type": "string"
                },
                {
                    "name": "tipo_log",
                    "description": "Tipo de logradouro",
                    "type": "enum",
                    "enums": [
                        { "value": "Alameda", "description": "Alameda" },
                        { "value": "Avenida", "description": "Avenida" },
                        { "value": "Estrada", "description": "Estrada" },
                        { "value": "Praça", "description": "Praça" },
                        { "value": "Quadra", "description": "Quadra" },
                        { "value": "Rodovia", "description": "Rodovia" },
                        { "value": "Rua", "description": "Rua" },
                        { "value": "Setor", "description": "Setor" },
                        { "value": "Travessa", "description": "Travessa" }
                    ]
                },
                {
                    "name": "logradouro",
                    "description": "Logradouro do endereço",
                    "type": "string"
                },
                {
                    "name": "num",
                    "description": "Número do endereço",
                    "type": "number",
                    "min": 0,
                    "max": 99999
                },
                {
                    "name": "compl",
                    "description": "Complemento do endereço",
                    "type": "string"
                },
                {
                    "name": "bairro",
                    "description": "Bairro do endereço",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "cep",
                    "description": "CEP do endereço",
                    "type": "string"
                },
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "nm_mun",
                    "description": "Nome do município",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "uf",
                    "description": "Unidade federativa",
                    "type": "enum",
                    "value_group_labels": {
                        "nordeste": "Nordeste",
                        "sul": "Sul",
                        "sudeste": "Sudeste",
                        "norte": "Norte",
                        "centro_oeste": "Centro-Oeste"
                    },
                    "enums": [
                        {
                            "value": "AC",
                            "description": "Acre",
                            "value_group": "norte"
                        },
                        {
                            "value": "AL",
                            "description": "Alagoas",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "AM",
                            "description": "Amazonas",
                            "value_group": "norte"
                        },
                        {
                            "value": "AP",
                            "description": "Amapá",
                            "value_group": "norte"
                        },
                        {
                            "value": "BA",
                            "description": "Bahia",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "CE",
                            "description": "Ceará",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "DF",
                            "description": "Distrito Federal",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "ES",
                            "description": "Espírito Santo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "GO",
                            "description": "Goiás",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MA",
                            "description": "Maranhão",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "MG",
                            "description": "Minas Gerais",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "MS",
                            "description": "Mato Grosso do Sul",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MT",
                            "description": "Mato Grosso",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "PA",
                            "description": "Pará",
                            "value_group": "norte"
                        },
                        {
                            "value": "PB",
                            "description": "Paraíba",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PE",
                            "description": "Pernambuco",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PI",
                            "description": "Piauí",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PR",
                            "description": "Paraná",
                            "value_group": "sul"
                        },
                        {
                            "value": "RJ",
                            "description": "Rio de Janeiro",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "RN",
                            "description": "Rio Grande do Norte",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "RO",
                            "description": "Rondônia",
                            "value_group": "norte"
                        },
                        {
                            "value": "RR",
                            "description": "Roraima",
                            "value_group": "norte"
                        },
                        {
                            "value": "RS",
                            "description": "Rio Grande do Sul",
                            "value_group": "sul"
                        },
                        {
                            "value": "SC",
                            "description": "Santa Catarina",
                            "value_group": "sul"
                        },
                        {
                            "value": "SE",
                            "description": "Sergipe",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "SP",
                            "description": "São Paulo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "TO",
                            "description": "Tocantins",
                            "value_group": "norte"
                        }
                    ]
                },
                {
                    "name": "end",
                    "description": "Endereço completo",
                    "type": "string"
                },
                {
                    "name": "tipo_geo",
                    "description": "Tipo de geometria",
                    "type": "string"
                },
                {
                    "name": "fonte_geo",
                    "description": "Fonte da geometria",
                    "type": "string"
                },
                {
                    "name": "geometry",
                    "type": "geometry",
                    "description": "Geometria espacial da localização do centro populacional",
                    "geometry_type": "POINT",
                    "distance_min_m": 500,
                    "distance_max_m": 10000,
                    "buffer_min_m": 500,
                    "buffer_max_m": 5000
                }
            ]
        },
        {
            "name": "cras",
            "columns": [
                {
                    "name": "nu_identif",
                    "description": "Número de identificação do CRAS",
                    "type": "number"
                },
                {
                    "name": "nm_cras",
                    "description": "Nome do CRAS",
                    "type": "string"
                },
                {
                    "name": "tipo_log",
                    "description": "Tipo de logradouro",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "Alameda", "description": "Alameda" },
                        { "value": "Avenida", "description": "Avenida" },
                        { "value": "Estrada", "description": "Estrada" },
                        { "value": "Praça", "description": "Praça" },
                        { "value": "Quadra", "description": "Quadra" },
                        { "value": "Rodovia", "description": "Rodovia" },
                        { "value": "Rua", "description": "Rua" },
                        { "value": "Setor", "description": "Setor" },
                        { "value": "Travessa", "description": "Travessa" }
                    ]
                },
                {
                    "name": "logradouro",
                    "description": "Logradouro do endereço",
                    "type": "string"
                },
                {
                    "name": "num",
                    "description": "Número do endereço",
                    "type": "string"
                },
                {
                    "name": "compl",
                    "description": "Complemento do endereço",
                    "type": "string"
                },
                {
                    "name": "bairro",
                    "description": "Bairro do endereço",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "cep",
                    "description": "CEP do endereço",
                    "type": "string"
                },
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "nm_mun",
                    "description": "Nome do município",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "uf",
                    "description": "Unidade federativa",
                    "type": "enum",
                    "value_group_labels": {
                        "nordeste": "Nordeste",
                        "sul": "Sul",
                        "sudeste": "Sudeste",
                        "norte": "Norte",
                        "centro_oeste": "Centro-Oeste"
                    },
                    "enums": [
                        {
                            "value": "AC",
                            "description": "Acre",
                            "value_group": "norte"
                        },
                        {
                            "value": "AL",
                            "description": "Alagoas",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "AM",
                            "description": "Amazonas",
                            "value_group": "norte"
                        },
                        {
                            "value": "AP",
                            "description": "Amapá",
                            "value_group": "norte"
                        },
                        {
                            "value": "BA",
                            "description": "Bahia",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "CE",
                            "description": "Ceará",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "DF",
                            "description": "Distrito Federal",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "ES",
                            "description": "Espírito Santo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "GO",
                            "description": "Goiás",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MA",
                            "description": "Maranhão",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "MG",
                            "description": "Minas Gerais",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "MS",
                            "description": "Mato Grosso do Sul",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MT",
                            "description": "Mato Grosso",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "PA",
                            "description": "Pará",
                            "value_group": "norte"
                        },
                        {
                            "value": "PB",
                            "description": "Paraíba",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PE",
                            "description": "Pernambuco",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PI",
                            "description": "Piauí",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PR",
                            "description": "Paraná",
                            "value_group": "sul"
                        },
                        {
                            "value": "RJ",
                            "description": "Rio de Janeiro",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "RN",
                            "description": "Rio Grande do Norte",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "RO",
                            "description": "Rondônia",
                            "value_group": "norte"
                        },
                        {
                            "value": "RR",
                            "description": "Roraima",
                            "value_group": "norte"
                        },
                        {
                            "value": "RS",
                            "description": "Rio Grande do Sul",
                            "value_group": "sul"
                        },
                        {
                            "value": "SC",
                            "description": "Santa Catarina",
                            "value_group": "sul"
                        },
                        {
                            "value": "SE",
                            "description": "Sergipe",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "SP",
                            "description": "São Paulo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "TO",
                            "description": "Tocantins",
                            "value_group": "norte"
                        }
                    ]
                },
                {
                    "name": "end",
                    "description": "Endereço completo",
                    "type": "string"
                },
                {
                    "name": "tipo_geo",
                    "description": "Tipo de geometria",
                    "type": "string"
                },
                {
                    "name": "fonte_geo",
                    "description": "Fonte da geometria",
                    "type": "string"
                },
                {
                    "name": "geometry",
                    "type": "geometry",
                    "description": "Geometria espacial da localização do CRAS",
                    "geometry_type": "POINT",
                    "distance_min_m": 100,
                    "distance_max_m": 3000,
                    "buffer_min_m": 100,
                    "buffer_max_m": 1500
                }
            ]
        },
        {
            "name": 'creas',
            "columns": [
                {
                    "name": 'ibge',
                    "description": 'Código correspondente do IBGE',
                    "type": 'number'
                },
                {
                    "name": 'nu_identif',
                    "description": 'Número identificador',
                    "type": 'number'
                },
                {
                    "name": 'nm_crea',
                    "description": 'Nome do Centro de Referência Especializado de Assistência Social',
                    "type": 'string',
                },
                {
                    "name": "tipo_log",
                    "description": "Tipo de logradouro",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "Alameda", "description": "Alameda" },
                        { "value": "Avenida", "description": "Avenida" },
                        { "value": "Estrada", "description": "Estrada" },
                        { "value": "Praça", "description": "Praça" },
                        { "value": "Quadra", "description": "Quadra" },
                        { "value": "Rodovia", "description": "Rodovia" },
                        { "value": "Rua", "description": "Rua" },
                        { "value": "Setor", "description": "Setor" },
                        { "value": "Travessa", "description": "Travessa" }
                    ]
                },
                {
                    "name": "logradouro",
                    "description": "Logradouro do endereço",
                    "type": "string"
                },
                {
                    "name": "num",
                    "description": "Número do endereço",
                    "type": "string"
                },
                {
                    "name": "compl",
                    "description": "Complemento do endereço",
                    "type": "string"
                },
                {
                    "name": "bairro",
                    "description": "Bairro do endereço",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "cep",
                    "description": "CEP do endereço",
                    "type": "string"
                },
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "nm_mun",
                    "description": "Nome do município",
                    "type": "string",
                    "semantic_group": "endereco_tipo"
                },
                {
                    "name": "uf",
                    "description": "Unidade federativa",
                    "type": "enum",
                    "value_group_labels": {
                        "nordeste": "Nordeste",
                        "sul": "Sul",
                        "sudeste": "Sudeste",
                        "norte": "Norte",
                        "centro_oeste": "Centro-Oeste"
                    },
                    "enums": [
                        {
                            "value": "AC",
                            "description": "Acre",
                            "value_group": "norte"
                        },
                        {
                            "value": "AL",
                            "description": "Alagoas",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "AM",
                            "description": "Amazonas",
                            "value_group": "norte"
                        },
                        {
                            "value": "AP",
                            "description": "Amapá",
                            "value_group": "norte"
                        },
                        {
                            "value": "BA",
                            "description": "Bahia",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "CE",
                            "description": "Ceará",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "DF",
                            "description": "Distrito Federal",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "ES",
                            "description": "Espírito Santo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "GO",
                            "description": "Goiás",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MA",
                            "description": "Maranhão",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "MG",
                            "description": "Minas Gerais",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "MS",
                            "description": "Mato Grosso do Sul",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MT",
                            "description": "Mato Grosso",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "PA",
                            "description": "Pará",
                            "value_group": "norte"
                        },
                        {
                            "value": "PB",
                            "description": "Paraíba",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PE",
                            "description": "Pernambuco",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PI",
                            "description": "Piauí",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PR",
                            "description": "Paraná",
                            "value_group": "sul"
                        },
                        {
                            "value": "RJ",
                            "description": "Rio de Janeiro",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "RN",
                            "description": "Rio Grande do Norte",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "RO",
                            "description": "Rondônia",
                            "value_group": "norte"
                        },
                        {
                            "value": "RR",
                            "description": "Roraima",
                            "value_group": "norte"
                        },
                        {
                            "value": "RS",
                            "description": "Rio Grande do Sul",
                            "value_group": "sul"
                        },
                        {
                            "value": "SC",
                            "description": "Santa Catarina",
                            "value_group": "sul"
                        },
                        {
                            "value": "SE",
                            "description": "Sergipe",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "SP",
                            "description": "São Paulo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "TO",
                            "description": "Tocantins",
                            "value_group": "norte"
                        }
                    ]
                },
                {
                    "name": "end",
                    "description": "Endereço completo",
                    "type": "string"
                },
                {
                    "name": "tipo_geo",
                    "description": "Tipo de geometria",
                    "type": "string"
                },
                {
                    "name": "fonte_geo",
                    "description": "Fonte da geometria",
                    "type": "string"
                },
                {
                    "name": "geometry",
                    "type": "geometry",
                    "description": "Geometria espacial da localização do CREAS",
                    "geometry_type": "POINT",
                    "distance_min_m": 500,
                    "distance_max_m": 5000,
                    "buffer_min_m": 500,
                    "buffer_max_m": 3000
                }
            ],
        },
        {
            "name": 'distrito',
            "columns": [
                {
                    "name": 'cd_dist',
                    "description": 'Código do Distrito',
                    "type": 'string',
                },
                {
                    "name": 'nm_dist',
                    "description": 'Nome do distrito',
                    "type": 'string',
                },
                {
                    "name": 'cd_mun',
                    "description": 'Código do Municipio',
                    "type": 'string',
                },
                {
                    "name": 'cd_concurb',
                    "description": 'Código da Concurb',
                    "type": 'string',
                },
                {
                    "name": "geometry",
                    "type": "geometry",
                    "description": "Geometria espacial do distrito",
                    "geometry_type": "MULTIPOLYGON",
                    "distance_min_m": 100,
                    "distance_max_m": 50000,
                    "buffer_min_m": 100,
                    "buffer_max_m": 5000
                }
            ],
        },
        {
            "name": "escola",
            "columns": [
                {
                    "name": "cd_entidade",
                    "description": "Código da entidade escolar",
                    "type": "number"
                },
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "cd_dist",
                    "description": "Código do distrito",
                    "type": "string"
                },
                {
                    "name": "nm_entidade",
                    "description": "Nome da entidade escolar",
                    "type": "string"
                },
                {
                    "name": "tp_depende",
                    "description": "Tipo de dependência administrativa",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Federal" },
                        { "value": "2", "description": "Estadual" },
                        { "value": "3", "description": "Municipal" },
                        { "value": "4", "description": "Particular" }
                    ]
                },
                {
                    "name": "tp_localiz",
                    "description": "Tipo de localização",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Urbana" },
                        { "value": "2", "description": "Rural" }
                    ]
                },
                {
                    "name": "tp_local_1",
                    "description": "Tipo de local de funcionamento",
                    "type": "number"
                },
                {
                    "name": "ds_enderec",
                    "description": "Descrição do endereço",
                    "type": "string"
                },
                {
                    "name": "ds_complem",
                    "description": "Descrição do complemento do endereço",
                    "type": "string"
                },
                {
                    "name": "nm_bairro",
                    "description": "Nome do bairro",
                    "type": "string"
                },
                {
                    "name": "cp_cep",
                    "description": "CEP do endereço",
                    "type": "string"
                },
                {
                    "name": "latitude",
                    "description": "Coordenada geográfica de latitude",
                    "type": "number",
                    "min": -33.75,
                    "max": 5.27
                },
                {
                    "name": "longitude",
                    "description": "Coordenada geográfica de longitude",
                    "type": "number",
                    "min": -73.99,
                    "max": -34.79
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial da localização",
                    "type": "string"
                }
            ]
        },
        {
            "name": "microdados_ed_basica",
            "columns": [
                {
                    "name": "cd_entidade",
                    "description": "Código da entidade escolar",
                    "type": "number"
                },
                {
                    "name": "tp_dependencia",
                    "description": "Tipo de dependência administrativa",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Federal" },
                        { "value": "2", "description": "Estadual" },
                        { "value": "3", "description": "Municipal" },
                        { "value": "4", "description": "Particular" }
                    ]
                },
                {
                    "name": "tp_categoria_escola_privada",
                    "description": "Tipo de categoria da escola privada",
                    "type": "number"
                },
                {
                    "name": "tp_localizacao",
                    "description": "Tipo de localização",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Urbana" },
                        { "value": "2", "description": "Rural" }
                    ]
                },
                {
                    "name": "tp_localizacao_diferenciada",
                    "description": "Tipo de localização diferenciada",
                    "type": "number"
                },
                {
                    "name": "nu_ddd",
                    "description": "Número de DDD do telefone",
                    "type": "number",
                    "min": 11,
                    "max": 99
                },
                {
                    "name": "nu_telefone",
                    "description": "Número de telefone",
                    "type": "number"
                },
                {
                    "name": "tp_situacao_funcionamento",
                    "description": "Tipo de situação de funcionamento",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Em Atividade" },
                        { "value": "2", "description": "Paralisada" },
                        { "value": "3", "description": "Extinta (ano do Censo)" },
                        { "value": "4", "description": "Extinta em Anos Anteriores" }
                    ]
                },
                {
                    "name": "co_orgao_regional",
                    "description": "Código do órgão regional",
                    "type": "string"
                },
                {
                    "name": "dt_ano_letivo_inicio",
                    "description": "Data de início do ano letivo",
                    "type": "string",
                    "semantic_group": "data_ano_letivo"
                },
                {
                    "name": "dt_ano_letivo_termino",
                    "description": "Data de término do ano letivo",
                    "type": "string",
                    "semantic_group": "data_ano_letivo"
                },
                {
                    "name": "in_vinculo_secretaria_educacao",
                    "description": "Indicador de vínculo com secretaria de educação",
                    "type": "binary",
                    "semantic_group": "vinculo_orgaos"
                },
                {
                    "name": "in_vinculo_seguranca_publica",
                    "description": "Indicador de vínculo com segurança pública",
                    "type": "binary",
                    "semantic_group": "vinculo_orgaos"
                },
                {
                    "name": "in_vinculo_secretaria_saude",
                    "description": "Indicador de vínculo com secretaria de saúde",
                    "type": "binary",
                    "semantic_group": "vinculo_orgaos"
                },
                {
                    "name": "in_vinculo_outro_orgao",
                    "description": "Indicador de vínculo com outro órgão",
                    "type": "binary",
                    "semantic_group": "vinculo_orgaos"
                },
                {
                    "name": "in_poder_publico_parceria",
                    "description": "Indicador de parceria com o poder público",
                    "type": "binary",
                    "semantic_group": "vinculo_orgaos"
                },
                {
                    "name": "tp_poder_publico_parceria",
                    "description": "Tipo de parceria com o poder público",
                    "type": "number"
                },
                {
                    "name": "in_forma_cont_termo_colabora",
                    "description": "Indicador de forma de contrato: termo de colaboração",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_termo_fomento",
                    "description": "Indicador de forma de contrato: termo de fomento",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_acordo_coop",
                    "description": "Indicador de forma de contrato: acordo de cooperação",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_prestacao_serv",
                    "description": "Indicador de forma de contrato: prestação de serviço",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_coop_tec_fin",
                    "description": "Indicador de forma de contrato: cooperação técnica e financeira",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_consorcio_pub",
                    "description": "Indicador de forma de contrato: consórcio público",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_mu_termo_colab",
                    "description": "Indicador de forma de contrato com município: termo de colaboração",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_mu_termo_fomento",
                    "description": "Indicador de forma de contrato com município: termo de fomento",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_mu_acordo_coop",
                    "description": "Indicador de forma de contrato com município: acordo de cooperação",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_mu_prest_serv",
                    "description": "Indicador de forma de contrato com município: prestação de serviço",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_mu_coop_tec_fin",
                    "description": "Indicador de forma de contrato com município: cooperação técnica e financeira",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_mu_consorcio_pub",
                    "description": "Indicador de forma de contrato com município: consórcio público",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_es_termo_colab",
                    "description": "Indicador de forma de contrato com estado: termo de colaboração",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_es_termo_fomento",
                    "description": "Indicador de forma de contrato com estado: termo de fomento",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_es_acordo_coop",
                    "description": "Indicador de forma de contrato com estado: acordo de cooperação",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_es_prest_serv",
                    "description": "Indicador de forma de contrato com estado: prestação de serviço",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_es_coop_tec_fin",
                    "description": "Indicador de forma de contrato com estado: cooperação técnica e financeira",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_forma_cont_es_consorcio_pub",
                    "description": "Indicador de forma de contrato com estado: consórcio público",
                    "type": "binary",
                    "semantic_group": "vinculo_contratos"
                },
                {
                    "name": "in_mant_escola_privada_emp",
                    "description": "Indicador de mantenedora da escola privada: empresa",
                    "type": "binary",
                    "semantic_group": "mantenedora_indicador"
                },
                {
                    "name": "in_mant_escola_privada_ong",
                    "description": "Indicador de mantenedora da escola privada: ONG",
                    "type": "binary",
                    "semantic_group": "mantenedora_indicador"
                },
                {
                    "name": "in_mant_escola_privada_oscip",
                    "description": "Indicador de mantenedora da escola privada: OSCIP",
                    "type": "binary",
                    "semantic_group": "mantenedora_indicador"
                },
                {
                    "name": "in_mant_escola_priv_ong_oscip",
                    "description": "Indicador de mantenedora da escola privada: ONG/OSCIP",
                    "type": "binary",
                    "semantic_group": "mantenedora_indicador"
                },
                {
                    "name": "in_mant_escola_privada_sind",
                    "description": "Indicador de mantenedora da escola privada: sindicato",
                    "type": "binary",
                    "semantic_group": "mantenedora_indicador"
                },
                {
                    "name": "in_mant_escola_privada_sist_s",
                    "description": "Indicador de mantenedora da escola privada: Sistema S",
                    "type": "binary",
                    "semantic_group": "mantenedora_indicador"
                },
                {
                    "name": "in_mant_escola_privada_s_fins",
                    "description": "Indicador de mantenedora da escola privada: sem fins lucrativos",
                    "type": "binary",
                    "semantic_group": "mantenedora_indicador"
                },
                {
                    "name": "nu_cnpj_escola_privada",
                    "description": "Número do CNPJ da escola privada",
                    "type": "string"
                },
                {
                    "name": "nu_cnpj_mantenedora",
                    "description": "Número do CNPJ da mantenedora",
                    "type": "string"
                },
                {
                    "name": "tp_regulamentacao",
                    "description": "Tipo de regulamentação",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "0", "description": "Não" },
                        { "value": "1", "description": "Sim" },
                        { "value": "2", "description": "Em tramitação" }
                    ]
                },
                {
                    "name": "tp_responsavel_regulamentacao",
                    "description": "Tipo de responsável pela regulamentação",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Federal" },
                        { "value": "2", "description": "Estadual" },
                        { "value": "3", "description": "Municipal" },
                        { "value": "4", "description": "Estadual e Municipal" },
                        { "value": "5", "description": "Federal e Estadual" },
                        { "value": "6", "description": "Federal, Estadual e Municipal" },
                        { "value": "9", "description": "Não informado" }
                    ]
                },
                {
                    "name": "co_escola_sede_vinculada",
                    "description": "Código da escola sede vinculada",
                    "type": "number"
                },
                {
                    "name": "co_ies_ofertante",
                    "description": "Código da IES ofertante",
                    "type": "number"
                },
                {
                    "name": "in_local_func_predio_escolar",
                    "description": "Indicador de local de funcionamento: prédio escolar",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "tp_ocupacao_predio_escolar",
                    "description": "Tipo de ocupação do prédio escolar",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Próprio" },
                        { "value": "2", "description": "Alugado" },
                        { "value": "3", "description": "Cedido" }
                    ]
                },
                {
                    "name": "in_local_func_socioeducativo",
                    "description": "Indicador de local de funcionamento: unidade socioeducativa",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "in_local_func_unid_prisional",
                    "description": "Indicador de local de funcionamento: unidade prisional",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "in_local_func_prisional_socio",
                    "description": "Indicador de local de funcionamento: unidade prisional/socioeducativa",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "in_local_func_galpao",
                    "description": "Indicador de local de funcionamento: galpão",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "tp_ocupacao_galpao",
                    "description": "Tipo de ocupação do galpão",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Próprio" },
                        { "value": "2", "description": "Alugado" },
                        { "value": "3", "description": "Cedido" },
                        { "value": "9", "description": "Sem declaração" }
                    ]
                },
                {
                    "name": "in_local_func_salas_outra_esc",
                    "description": "Indicador de local de funcionamento: salas em outra escola",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "in_local_func_outros",
                    "description": "Indicador de local de funcionamento: outros",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "in_predio_compartilhado",
                    "description": "Indicador de prédio compartilhado",
                    "type": "binary",
                    "semantic_group": "indicador_local_funcionamento"
                },
                {
                    "name": "in_agua_potavel",
                    "description": "Indicador de água potável",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_agua_rede_publica",
                    "description": "Indicador de abastecimento de água por rede pública",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_agua_poco_artesiano",
                    "description": "Indicador de abastecimento de água por poço artesiano",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_agua_cacimba",
                    "description": "Indicador de abastecimento de água por cacimba/cisterna/poço",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_agua_fonte_rio",
                    "description": "Indicador de abastecimento de água por fonte/rio/igarapé",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_agua_inexistente",
                    "description": "Indicador de abastecimento de água inexistente",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_agua_carro_pipa",
                    "description": "Indicador de abastecimento de água por carro-pipa",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_energia_rede_publica",
                    "description": "Indicador de energia elétrica por rede pública",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_energia_gerador_fossil",
                    "description": "Indicador de energia elétrica por gerador a combustível fóssil",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_energia_renovavel",
                    "description": "Indicador de energia elétrica por fontes renováveis",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_energia_inexistente",
                    "description": "Indicador de energia elétrica inexistente",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_esgoto_rede_publica",
                    "description": "Indicador de esgotamento sanitário por rede pública",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_esgoto_fossa_septica",
                    "description": "Indicador de esgotamento sanitário por fossa séptica",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_esgoto_fossa_comum",
                    "description": "Indicador de esgotamento sanitário por fossa comum",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_esgoto_fossa",
                    "description": "Indicador de esgotamento sanitário por fossa",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_esgoto_inexistente",
                    "description": "Indicador de esgotamento sanitário inexistente",
                    "type": "binary",
                    "semantic_group": "indicador_higiene"
                },
                {
                    "name": "in_lixo_servico_coleta",
                    "description": "Indicador de destinação do lixo: serviço de coleta",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_lixo_queima",
                    "description": "Indicador de destinação do lixo: queima",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_lixo_enterra",
                    "description": "Indicador de destinação do lixo: enterra",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_lixo_destino_final_publico",
                    "description": "Indicador de destinação do lixo: destino final público",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_lixo_descarta_outra_area",
                    "description": "Indicador de destinação do lixo: descarte em outra área",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_tratamento_lixo_separacao",
                    "description": "Indicador de tratamento do lixo: separação",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_tratamento_lixo_reutiliza",
                    "description": "Indicador de tratamento do lixo: reutilização",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_tratamento_lixo_reciclagem",
                    "description": "Indicador de tratamento do lixo: reciclagem",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_tratamento_lixo_inexistente",
                    "description": "Indicador de tratamento do lixo inexistente",
                    "type": "binary",
                    "semantic_group": "indicador_lixo"
                },
                {
                    "name": "in_almoxarifado",
                    "description": "Indicador de dependência: almoxarifado",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_area_verde",
                    "description": "Indicador de dependência: área verde",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_area_plantio",
                    "description": "Indicador de dependência: área de plantio",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_auditorio",
                    "description": "Indicador de dependência: auditório",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_banheiro",
                    "description": "Indicador de dependência: banheiro",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_banheiro_ei",
                    "description": "Indicador de dependência: banheiro para educação infantil",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_banheiro_pne",
                    "description": "Indicador de dependência: banheiro para PNE",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_banheiro_funcionarios",
                    "description": "Indicador de dependência: banheiro para funcionários",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_banheiro_chuveiro",
                    "description": "Indicador de dependência: banheiro com chuveiro",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_biblioteca",
                    "description": "Indicador de dependência: biblioteca",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_biblioteca_sala_leitura",
                    "description": "Indicador de dependência: biblioteca/sala de leitura",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_cozinha",
                    "description": "Indicador de dependência: cozinha",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_despensa",
                    "description": "Indicador de dependência: despensa",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_dormitorio_aluno",
                    "description": "Indicador de dependência: dormitório de aluno",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_dormitorio_professor",
                    "description": "Indicador de dependência: dormitório de professor",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_laboratorio_ciencias",
                    "description": "Indicador de dependência: laboratório de ciências",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_laboratorio_informatica",
                    "description": "Indicador de dependência: laboratório de informática",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_laboratorio_educ_prof",
                    "description": "Indicador de dependência: laboratório de educação profissional",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_patio_coberto",
                    "description": "Indicador de dependência: pátio coberto",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_patio_descoberto",
                    "description": "Indicador de dependência: pátio descoberto",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_parque_infantil",
                    "description": "Indicador de dependência: parque infantil",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_piscina",
                    "description": "Indicador de dependência: piscina",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_quadra_esportes",
                    "description": "Indicador de dependência: quadra de esportes",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_quadra_esportes_coberta",
                    "description": "Indicador de dependência: quadra de esportes coberta",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_quadra_esportes_descoberta",
                    "description": "Indicador de dependência: quadra de esportes descoberta",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_refeitorio",
                    "description": "Indicador de dependência: refeitório",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_atelie_artes",
                    "description": "Indicador de dependência: sala/ateliê de artes",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_musica_coral",
                    "description": "Indicador de dependência: sala de música/coral",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_estudio_danca",
                    "description": "Indicador de dependência: sala/estúdio de dança",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_multiuso",
                    "description": "Indicador de dependência: sala multiuso",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_estudio_gravacao",
                    "description": "Indicador de dependência: sala/estúdio de gravação",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_oficinas_educ_prof",
                    "description": "Indicador de dependência: sala de oficinas de educação profissional",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_diretoria",
                    "description": "Indicador de dependência: sala de diretoria",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_leitura",
                    "description": "Indicador de dependência: sala de leitura",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_professor",
                    "description": "Indicador de dependência: sala de professor",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_repouso_aluno",
                    "description": "Indicador de dependência: sala de repouso do aluno",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_secretaria",
                    "description": "Indicador de dependência: secretaria",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_sala_atendimento_especial",
                    "description": "Indicador de dependência: sala de atendimento especial",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_terreirao",
                    "description": "Indicador de dependência: terreirão",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_viveiro",
                    "description": "Indicador de dependência: viveiro",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_dependencias_outras",
                    "description": "Indicador de dependências: outras",
                    "type": "binary",
                    "semantic_group": "indicador_infra"
                },
                {
                    "name": "in_acessibilidade_corrimao",
                    "description": "Indicador de acessibilidade: corrimão",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_elevador",
                    "description": "Indicador de acessibilidade: elevador",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_pisos_tateis",
                    "description": "Indicador de acessibilidade: pisos táteis",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_vao_livre",
                    "description": "Indicador de acessibilidade: vão livre",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_rampas",
                    "description": "Indicador de acessibilidade: rampas",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_sinal_sonoro",
                    "description": "Indicador de acessibilidade: sinal sonoro",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_sinal_tatil",
                    "description": "Indicador de acessibilidade: sinal tátil",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_sinal_visual",
                    "description": "Indicador de acessibilidade: sinal visual",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_inexistente",
                    "description": "Indicador de acessibilidade inexistente",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "in_acessibilidade_sinalizacao",
                    "description": "Indicador de acessibilidade: sinalização",
                    "type": "binary",
                    "semantic_group": "indicador_acessibilidade"
                },
                {
                    "name": "qt_salas_utilizadas_dentro",
                    "description": "Quantidade de salas utilizadas dentro do prédio",
                    "type": "number",
                    "semantic_group": "quantidade_salas"
                },
                {
                    "name": "qt_salas_utilizadas_fora",
                    "description": "Quantidade de salas utilizadas fora do prédio",
                    "type": "number",
                    "semantic_group": "quantidade_salas"
                },
                {
                    "name": "qt_salas_utilizadas",
                    "description": "Quantidade de salas utilizadas",
                    "type": "number",
                    "semantic_group": "quantidade_salas"
                },
                {
                    "name": "qt_salas_utiliza_climatizadas",
                    "description": "Quantidade de salas utilizadas climatizadas",
                    "type": "number",
                    "semantic_group": "quantidade_salas"
                },
                {
                    "name": "qt_salas_utilizadas_acessiveis",
                    "description": "Quantidade de salas utilizadas acessíveis",
                    "type": "number",
                    "semantic_group": "quantidade_salas"
                },
                {
                    "name": "in_equip_parabolica",
                    "description": "Indicador de equipamento: parabólica",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_computador",
                    "description": "Indicador de equipamento: computador",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_copiadora",
                    "description": "Indicador de equipamento: copiadora",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_impressora",
                    "description": "Indicador de equipamento: impressora",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_impressora_mult",
                    "description": "Indicador de equipamento: impressora multifuncional",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_scanner",
                    "description": "Indicador de equipamento: scanner",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_nenhum",
                    "description": "Indicador de equipamento: nenhum",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_dvd",
                    "description": "Indicador de equipamento: DVD",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_equip_dvd",
                    "description": "Quantidade de equipamentos de DVD",
                    "type": "number",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_som",
                    "description": "Indicador de equipamento: som",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_equip_som",
                    "description": "Quantidade de equipamentos de som",
                    "type": "number",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_equip_tv",
                    "description": "Indicador de equipamento: TV",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_equip_tv",
                    "description": "Quantidade de equipamentos de TV",
                    "type": "number",
                    "semantic_group": "quantidade_equipamentos"
                },
                {
                    "name": "in_equip_lousa_digital",
                    "description": "Indicador de equipamento: lousa digital",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_equip_lousa_digital",
                    "description": "Quantidade de lousas digitais",
                    "type": "number",
                    "semantic_group": "quantidade_equipamentos"
                },
                {
                    "name": "in_equip_multimidia",
                    "description": "Indicador de equipamento: projetor multimídia",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_equip_multimidia",
                    "description": "Quantidade de projetores multimídia",
                    "type": "number",
                    "semantic_group": "quantidade_equipamentos"
                },
                {
                    "name": "in_desktop_aluno",
                    "description": "Indicador de computador desktop para aluno",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_desktop_aluno",
                    "description": "Quantidade de computadores desktop para aluno",
                    "type": "number",
                    "semantic_group": "quantidade_equipamentos"
                },
                {
                    "name": "in_comp_portatil_aluno",
                    "description": "Indicador de computador portátil para aluno",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_comp_portatil_aluno",
                    "description": "Quantidade de computadores portáteis para aluno",
                    "type": "number",
                    "semantic_group": "quantidade_equipamentos"
                },
                {
                    "name": "in_tablet_aluno",
                    "description": "Indicador de tablet para aluno",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "qt_tablet_aluno",
                    "description": "Quantidade de tablets para aluno",
                    "type": "number",
                    "semantic_group": "quantidade_equipamentos"
                },
                {
                    "name": "in_internet",
                    "description": "Indicador de acesso à internet",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_internet_alunos",
                    "description": "Indicador de acesso à internet para alunos",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_internet_administrativo",
                    "description": "Indicador de acesso à internet para uso administrativo",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_internet_aprendizagem",
                    "description": "Indicador de acesso à internet para aprendizagem",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_internet_comunidade",
                    "description": "Indicador de acesso à internet para a comunidade",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_acesso_internet_computador",
                    "description": "Indicador de acesso à internet por computador",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_aces_internet_disp_pessoais",
                    "description": "Indicador de acesso à internet por dispositivos pessoais",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "tp_rede_local",
                    "description": "Tipo de rede local",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "0", "description": "Não há rede local interligando computadores" },
                        { "value": "1", "description": "A cabo" },
                        { "value": "2", "description": "Wireless" },
                        { "value": "3", "description": "A cabo e Wireless" },
                        { "value": "9", "description": "Não informado" }
                    ]
                },
                {
                    "name": "in_banda_larga",
                    "description": "Indicador de acesso à internet banda larga",
                    "type": "binary",
                    "semantic_group": "indicador_equipamentos"
                },
                {
                    "name": "in_prof_administrativos",
                    "description": "Indicador de profissional: administrativos",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_administrativos",
                    "description": "Quantidade de profissionais administrativos",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_servicos_gerais",
                    "description": "Indicador de profissional: serviços gerais",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_servicos_gerais",
                    "description": "Quantidade de profissionais de serviços gerais",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_bibliotecario",
                    "description": "Indicador de profissional: bibliotecário",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_bibliotecario",
                    "description": "Quantidade de profissionais bibliotecários",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_saude",
                    "description": "Indicador de profissional: saúde",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_saude",
                    "description": "Quantidade de profissionais de saúde",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_coordenador",
                    "description": "Indicador de profissional: coordenador",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_coordenador",
                    "description": "Quantidade de coordenadores",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_fonaudiologo",
                    "description": "Indicador de profissional: fonoaudiólogo",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_fonaudiologo",
                    "description": "Quantidade de fonoaudiólogos",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_nutricionista",
                    "description": "Indicador de profissional: nutricionista",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_nutricionista",
                    "description": "Quantidade de nutricionistas",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_psicologo",
                    "description": "Indicador de profissional: psicólogo",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_psicologo",
                    "description": "Quantidade de psicólogos",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_alimentacao",
                    "description": "Indicador de profissional: alimentação",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_alimentacao",
                    "description": "Quantidade de profissionais de alimentação",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_pedagogia",
                    "description": "Indicador de profissional: pedagogia",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_pedagogia",
                    "description": "Quantidade de profissionais de pedagogia",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_secretario",
                    "description": "Indicador de profissional: secretário",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_secretario",
                    "description": "Quantidade de secretários",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_seguranca",
                    "description": "Indicador de profissional: segurança",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_seguranca",
                    "description": "Quantidade de profissionais de segurança",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_monitores",
                    "description": "Indicador de profissional: monitores",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_monitores",
                    "description": "Quantidade de monitores",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_gestao",
                    "description": "Indicador de profissional: gestão",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_gestao",
                    "description": "Quantidade de profissionais de gestão",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_assist_social",
                    "description": "Indicador de profissional: assistente social",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_assist_social",
                    "description": "Quantidade de assistentes sociais",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_trad_libras",
                    "description": "Indicador de profissional: tradutor de libras",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_trad_libras",
                    "description": "Quantidade de tradutores de libras",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_agricola",
                    "description": "Indicador de profissional: agrícola",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_agricola",
                    "description": "Quantidade de profissionais agrícolas",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_prof_revisor_braille",
                    "description": "Indicador de profissional: revisor braille",
                    "type": "binary",
                    "semantic_group": "indicador_profissionais"
                },
                {
                    "name": "qt_prof_revisor_braille",
                    "description": "Quantidade de revisores braille",
                    "type": "number",
                    "semantic_group": "quantidade_profissionais"
                },
                {
                    "name": "in_alimentacao",
                    "description": "Indicador de alimentação escolar",
                    "type": "binary",
                },
                {
                    "name": "in_material_ped_multimidia",
                    "description": "Indicador de material pedagógico: multimídia",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_infantil",
                    "description": "Indicador de material pedagógico: educação infantil",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_cientifico",
                    "description": "Indicador de material pedagógico: científico",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_difusao",
                    "description": "Indicador de material pedagógico: difusão cultural e artística",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_musical",
                    "description": "Indicador de material pedagógico: musical",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_jogos",
                    "description": "Indicador de material pedagógico: jogos educativos",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_artisticas",
                    "description": "Indicador de material pedagógico: artes e artesanato",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_profissional",
                    "description": "Indicador de material pedagógico: educação profissional",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_desportiva",
                    "description": "Indicador de material pedagógico: prática desportiva",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_indigena",
                    "description": "Indicador de material pedagógico: educação indígena",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_etnico",
                    "description": "Indicador de material pedagógico: relações étnico-raciais",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_campo",
                    "description": "Indicador de material pedagógico: educação do campo",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_bil_surdos",
                    "description": "Indicador de material pedagógico: educação bilíngue de surdos",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_agricola",
                    "description": "Indicador de material pedagógico: educação agrícola",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_quilombola",
                    "description": "Indicador de material pedagógico: educação quilombola",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_edu_esp",
                    "description": "Indicador de material pedagógico: educação especial",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_material_ped_nenhum",
                    "description": "Indicador de material pedagógico: nenhum",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "in_educacao_indigena",
                    "description": "Indicador de educação indígena",
                    "type": "binary",
                    "semantic_group": "indicador_material"
                },
                {
                    "name": "tp_indigena_lingua",
                    "description": "Tipo de língua indígena",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "1", "description": "Somente em Língua Indígena" },
                        { "value": "2", "description": "Somente em Língua Portuguesa" },
                        { "value": "3", "description": "Em Língua Indígena e em Língua Portuguesa" }
                    ]
                },
                {
                    "name": "co_lingua_indigena_1",
                    "description": "Código da língua indígena 1",
                    "type": "number",
                },
                {
                    "name": "co_lingua_indigena_2",
                    "description": "Código da língua indígena 2",
                    "type": "number",
                },
                {
                    "name": "co_lingua_indigena_3",
                    "description": "Código da língua indígena 3",
                    "type": "number",
                },
                {
                    "name": "in_exame_selecao",
                    "description": "Indicador de exame de seleção",
                    "type": "binary",
                    "semantic_group": "indicador_ingresso"
                },
                {
                    "name": "in_reserva_ppi",
                    "description": "Indicador de reserva de vagas: pretos, pardos e indígenas",
                    "type": "binary",
                    "semantic_group": "indicador_ingresso"
                },
                {
                    "name": "in_reserva_renda",
                    "description": "Indicador de reserva de vagas: renda",
                    "type": "binary",
                    "semantic_group": "indicador_ingresso"
                },
                {
                    "name": "in_reserva_publica",
                    "description": "Indicador de reserva de vagas: escola pública",
                    "type": "binary",
                    "semantic_group": "indicador_ingresso"
                },
                {
                    "name": "in_reserva_pcd",
                    "description": "Indicador de reserva de vagas: pessoa com deficiência",
                    "type": "binary",
                    "semantic_group": "indicador_ingresso"
                },
                {
                    "name": "in_reserva_outros",
                    "description": "Indicador de reserva de vagas: outros",
                    "type": "binary",
                    "semantic_group": "indicador_ingresso"
                },
                {
                    "name": "in_reserva_nenhuma",
                    "description": "Indicador de reserva de vagas: nenhuma",
                    "type": "binary",
                    "semantic_group": "indicador_ingresso"
                },
                {
                    "name": "in_redes_sociais",
                    "description": "Indicador de presença em redes sociais",
                    "type": "binary",
                    "semantic_group": "indicador_compartilhamento"
                },
                {
                    "name": "in_espaco_atividade",
                    "description": "Indicador de compartilhamento de espaços para atividades",
                    "type": "binary",
                    "semantic_group": "indicador_compartilhamento"
                },
                {
                    "name": "in_espaco_equipamento",
                    "description": "Indicador de compartilhamento de espaços e equipamentos",
                    "type": "binary",
                    "semantic_group": "indicador_compartilhamento"
                },
                {
                    "name": "in_orgao_ass_pais",
                    "description": "Indicador de órgão colegiado: associação de pais",
                    "type": "binary",
                    "semantic_group": "indicador_orgao"
                },
                {
                    "name": "in_orgao_ass_pais_mestres",
                    "description": "Indicador de órgão colegiado: associação de pais e mestres",
                    "type": "binary",
                    "semantic_group": "indicador_orgao"
                },
                {
                    "name": "in_orgao_conselho_escolar",
                    "description": "Indicador de órgão colegiado: conselho escolar",
                    "type": "binary",
                    "semantic_group": "indicador_orgao"
                },
                {
                    "name": "in_orgao_gremio_estudantil",
                    "description": "Indicador de órgão colegiado: grêmio estudantil",
                    "type": "binary",
                    "semantic_group": "indicador_orgao"
                },
                {
                    "name": "in_orgao_outros",
                    "description": "Indicador de órgão colegiado: outros",
                    "type": "binary",
                    "semantic_group": "indicador_orgao"
                },
                {
                    "name": "in_orgao_nenhum",
                    "description": "Indicador de órgão colegiado: nenhum",
                    "type": "binary",
                    "semantic_group": "indicador_orgao"
                },
                {
                    "name": "tp_proposta_pedagogica",
                    "description": "Tipo de proposta pedagógica",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "0", "description": "Não" },
                        { "value": "1", "description": "Sim" },
                        { "value": "2", "description": "A escola não possui projeto político pedagógico/proposta pedagógica" },
                        { "value": "9", "description": "Não informado" }
                    ]
                },
                {
                    "name": "in_educ_ambiental",
                    "description": "Indicador de educação ambiental",
                    "type": "binary",
                    "semantic_group": "indicador_ambiental"
                },
                {
                    "name": "in_educ_amb_conteudo",
                    "description": "Indicador de educação ambiental: conteúdo",
                    "type": "binary",
                    "semantic_group": "indicador_ambiental"
                },
                {
                    "name": "in_educ_amb_curricular",
                    "description": "Indicador de educação ambiental: projeto curricular",
                    "type": "binary",
                    "semantic_group": "indicador_ambiental"
                },
                {
                    "name": "in_educ_amb_eixo",
                    "description": "Indicador de educação ambiental: eixo norteador",
                    "type": "binary",
                    "semantic_group": "indicador_ambiental"
                },
                {
                    "name": "in_educ_amb_eventos",
                    "description": "Indicador de educação ambiental: eventos",
                    "type": "binary",
                    "semantic_group": "indicador_ambiental"
                },
                {
                    "name": "in_educ_amb_projetos",
                    "description": "Indicador de educação ambiental: projetos",
                    "type": "binary",
                    "semantic_group": "indicador_ambiental"
                },
                {
                    "name": "in_educ_amb_nenhuma",
                    "description": "Indicador de educação ambiental: nenhuma",
                    "type": "binary",
                    "semantic_group": "indicador_ambiental"
                },
                {
                    "name": "tp_aee",
                    "description": "Tipo de atendimento educacional especializado",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "0", "description": "Não oferece" },
                        { "value": "1", "description": "Não exclusivamente" },
                        { "value": "2", "description": "Exclusivamente" }
                    ]
                },
                {
                    "name": "tp_atividade_complementar",
                    "description": "Tipo de atividade complementar",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "0", "description": "Não oferece" },
                        { "value": "1", "description": "Não exclusivamente" },
                        { "value": "2", "description": "Exclusivamente" }
                    ]
                },
                {
                    "name": "in_mediacao_presencial",
                    "description": "Indicador de mediação presencial",
                    "type": "binary",
                    "semantic_group": "indicador_mediacao"
                },
                {
                    "name": "in_mediacao_semipresencial",
                    "description": "Indicador de mediação semipresencial",
                    "type": "binary",
                    "semantic_group": "indicador_mediacao"
                },
                {
                    "name": "in_mediacao_ead",
                    "description": "Indicador de mediação por EAD",
                    "type": "binary",
                    "semantic_group": "indicador_mediacao"
                },
                {
                    "name": "in_regular",
                    "description": "Indicador de oferta de ensino regular",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_diurno",
                    "description": "Indicador de turno diurno",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_noturno",
                    "description": "Indicador de turno noturno",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_ead",
                    "description": "Indicador de oferta de EAD",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_escolarizacao",
                    "description": "Indicador de escolarização",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_inf",
                    "description": "Indicador de oferta de educação infantil",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_inf_cre",
                    "description": "Indicador de oferta de educação infantil: creche",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_inf_pre",
                    "description": "Indicador de oferta de educação infantil: pré-escola",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_fund",
                    "description": "Indicador de oferta de ensino fundamental",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_fund_ai",
                    "description": "Indicador de oferta de ensino fundamental: anos iniciais",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_fund_af",
                    "description": "Indicador de oferta de ensino fundamental: anos finais",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_med",
                    "description": "Indicador de oferta de ensino médio",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_prof",
                    "description": "Indicador de oferta de educação profissional",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_prof_tec",
                    "description": "Indicador de oferta de educação profissional técnica",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_eja",
                    "description": "Indicador de oferta de EJA",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_eja_fund",
                    "description": "Indicador de oferta de EJA: ensino fundamental",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_eja_med",
                    "description": "Indicador de oferta de EJA: ensino médio",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_esp",
                    "description": "Indicador de oferta de educação especial",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_esp_cc",
                    "description": "Indicador de oferta de educação especial: classes comuns",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "in_esp_ce",
                    "description": "Indicador de oferta de educação especial: classes especiais",
                    "type": "binary",
                    "semantic_group": "indicador_oferta"
                },
                {
                    "name": "qt_mat_bas",
                    "description": "Quantidade de matrículas na educação básica",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_inf",
                    "description": "Quantidade de matrículas na educação infantil",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_inf_cre",
                    "description": "Quantidade de matrículas na educação infantil: creche",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_inf_pre",
                    "description": "Quantidade de matrículas na educação infantil: pré-escola",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund",
                    "description": "Quantidade de matrículas no ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_ai",
                    "description": "Quantidade de matrículas no ensino fundamental: anos iniciais",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_ai_1",
                    "description": "Quantidade de matrículas no 1º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_ai_2",
                    "description": "Quantidade de matrículas no 2º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_ai_3",
                    "description": "Quantidade de matrículas no 3º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_ai_4",
                    "description": "Quantidade de matrículas no 4º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_ai_5",
                    "description": "Quantidade de matrículas no 5º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_af",
                    "description": "Quantidade de matrículas no ensino fundamental: anos finais",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_af_6",
                    "description": "Quantidade de matrículas no 6º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_af_7",
                    "description": "Quantidade de matrículas no 7º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_af_8",
                    "description": "Quantidade de matrículas no 8º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_af_9",
                    "description": "Quantidade de matrículas no 9º ano do ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med",
                    "description": "Quantidade de matrículas no ensino médio",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_prop",
                    "description": "Quantidade de matrículas no ensino médio propedêutico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_prop_1",
                    "description": "Quantidade de matrículas na 1ª série do ensino médio propedêutico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_prop_2",
                    "description": "Quantidade de matrículas na 2ª série do ensino médio propedêutico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_prop_3",
                    "description": "Quantidade de matrículas na 3ª série do ensino médio propedêutico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_prop_4",
                    "description": "Quantidade de matrículas na 4ª série do ensino médio propedêutico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_prop_ns",
                    "description": "Quantidade de matrículas no ensino médio propedêutico não seriado",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_ct",
                    "description": "Quantidade de matrículas no ensino médio: curso técnico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_ct_1",
                    "description": "Quantidade de matrículas na 1ª série do ensino médio: curso técnico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_ct_2",
                    "description": "Quantidade de matrículas na 2ª série do ensino médio: curso técnico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_ct_3",
                    "description": "Quantidade de matrículas na 3ª série do ensino médio: curso técnico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_ct_4",
                    "description": "Quantidade de matrículas na 4ª série do ensino médio: curso técnico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_ct_ns",
                    "description": "Quantidade de matrículas no ensino médio: curso técnico não seriado",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_nm",
                    "description": "Quantidade de matrículas no ensino médio: normal/magistério",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_nm_1",
                    "description": "Quantidade de matrículas na 1ª série do ensino médio: normal/magistério",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_nm_2",
                    "description": "Quantidade de matrículas na 2ª série do ensino médio: normal/magistério",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_nm_3",
                    "description": "Quantidade de matrículas na 3ª série do ensino médio: normal/magistério",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_nm_4",
                    "description": "Quantidade de matrículas na 4ª série do ensino médio: normal/magistério",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_prof",
                    "description": "Quantidade de matrículas na educação profissional",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_prof_tec",
                    "description": "Quantidade de matrículas na educação profissional técnica",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_prof_tec_conc",
                    "description": "Quantidade de matrículas na educação profissional técnica concomitante",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_prof_tec_subs",
                    "description": "Quantidade de matrículas na educação profissional técnica subsequente",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_prof_fic_conc",
                    "description": "Quantidade de matrículas na educação profissional FIC concomitante",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja",
                    "description": "Quantidade de matrículas na EJA",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_fund",
                    "description": "Quantidade de matrículas na EJA: ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_fund_ai",
                    "description": "Quantidade de matrículas na EJA: ensino fundamental anos iniciais",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_fund_af",
                    "description": "Quantidade de matrículas na EJA: ensino fundamental anos finais",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_fund_fic",
                    "description": "Quantidade de matrículas na EJA: ensino fundamental FIC",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_med",
                    "description": "Quantidade de matrículas na EJA: ensino médio",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_med_nprof",
                    "description": "Quantidade de matrículas na EJA: ensino médio não profissionalizante",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_med_fic",
                    "description": "Quantidade de matrículas na EJA: ensino médio FIC",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_eja_med_tec",
                    "description": "Quantidade de matrículas na EJA: ensino médio técnico",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_esp",
                    "description": "Quantidade de matrículas na educação especial",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_esp_cc",
                    "description": "Quantidade de matrículas na educação especial: classes comuns",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_esp_ce",
                    "description": "Quantidade de matrículas na educação especial: classes especiais",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_fem",
                    "description": "Quantidade de matrículas na educação básica do sexo feminino",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_masc",
                    "description": "Quantidade de matrículas na educação básica do sexo masculino",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_nd",
                    "description": "Quantidade de matrículas na educação básica de sexo não declarado",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_branca",
                    "description": "Quantidade de matrículas na educação básica de cor/raça branca",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_preta",
                    "description": "Quantidade de matrículas na educação básica de cor/raça preta",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_parda",
                    "description": "Quantidade de matrículas na educação básica de cor/raça parda",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_amarela",
                    "description": "Quantidade de matrículas na educação básica de cor/raça amarela",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_indigena",
                    "description": "Quantidade de matrículas na educação básica de cor/raça indígena",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_0_3",
                    "description": "Quantidade de matrículas na educação básica de 0 a 3 anos",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_4_5",
                    "description": "Quantidade de matrículas na educação básica de 4 a 5 anos",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_6_10",
                    "description": "Quantidade de matrículas na educação básica de 6 a 10 anos",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_11_14",
                    "description": "Quantidade de matrículas na educação básica de 11 a 14 anos",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_15_17",
                    "description": "Quantidade de matrículas na educação básica de 15 a 17 anos",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_18_mais",
                    "description": "Quantidade de matrículas na educação básica de 18 anos ou mais",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_d",
                    "description": "Quantidade de matrículas na educação básica no turno diurno",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_n",
                    "description": "Quantidade de matrículas na educação básica no turno noturno",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_bas_ead",
                    "description": "Quantidade de matrículas na educação básica em EAD",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_inf_int",
                    "description": "Quantidade de matrículas na educação infantil em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_inf_cre_int",
                    "description": "Quantidade de matrículas na creche em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_inf_pre_int",
                    "description": "Quantidade de matrículas na pré-escola em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_int",
                    "description": "Quantidade de matrículas no ensino fundamental em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_ai_int",
                    "description": "Quantidade de matrículas no ensino fundamental anos iniciais em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_fund_af_int",
                    "description": "Quantidade de matrículas no ensino fundamental anos finais em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_med_int",
                    "description": "Quantidade de matrículas no ensino médio em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_zr_urb",
                    "description": "Quantidade de matrículas em zona residencial urbana",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_zr_rur",
                    "description": "Quantidade de matrículas em zona residencial rural",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_mat_zr_na",
                    "description": "Quantidade de matrículas em zona residencial não aplicável",
                    "type": "number",
                    "semantic_group": "quantidade_matriculas"
                },
                {
                    "name": "qt_transp_publico",
                    "description": "Quantidade de alunos que utilizam transporte público",
                    "type": "number",
                    "semantic_group": "quantidade_social"
                },
                {
                    "name": "qt_transp_resp_est",
                    "description": "Quantidade de alunos que utilizam transporte de responsabilidade estadual",
                    "type": "number",
                    "semantic_group": "quantidade_social"
                },
                {
                    "name": "qt_transp_resp_mun",
                    "description": "Quantidade de alunos que utilizam transporte de responsabilidade municipal",
                    "type": "number",
                    "semantic_group": "quantidade_social"
                },
                {
                    "name": "qt_doc_bas",
                    "description": "Quantidade de docentes na educação básica",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_inf",
                    "description": "Quantidade de docentes na educação infantil",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_inf_cre",
                    "description": "Quantidade de docentes na educação infantil: creche",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_inf_pre",
                    "description": "Quantidade de docentes na educação infantil: pré-escola",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_fund",
                    "description": "Quantidade de docentes no ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_fund_ai",
                    "description": "Quantidade de docentes no ensino fundamental: anos iniciais",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_fund_af",
                    "description": "Quantidade de docentes no ensino fundamental: anos finais",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_med",
                    "description": "Quantidade de docentes no ensino médio",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_prof",
                    "description": "Quantidade de docentes na educação profissional",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_prof_tec",
                    "description": "Quantidade de docentes na educação profissional técnica",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_eja",
                    "description": "Quantidade de docentes na EJA",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_eja_fund",
                    "description": "Quantidade de docentes na EJA: ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_eja_med",
                    "description": "Quantidade de docentes na EJA: ensino médio",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_esp",
                    "description": "Quantidade de docentes na educação especial",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_esp_cc",
                    "description": "Quantidade de docentes na educação especial: classes comuns",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_doc_esp_ce",
                    "description": "Quantidade de docentes na educação especial: classes especiais",
                    "type": "number",
                    "semantic_group": "quantidade_profs"
                },
                {
                    "name": "qt_tur_bas",
                    "description": "Quantidade de turmas na educação básica",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_inf",
                    "description": "Quantidade de turmas na educação infantil",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_inf_cre",
                    "description": "Quantidade de turmas na educação infantil: creche",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_inf_pre",
                    "description": "Quantidade de turmas na educação infantil: pré-escola",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_fund",
                    "description": "Quantidade de turmas no ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_fund_ai",
                    "description": "Quantidade de turmas no ensino fundamental: anos iniciais",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_fund_af",
                    "description": "Quantidade de turmas no ensino fundamental: anos finais",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_med",
                    "description": "Quantidade de turmas no ensino médio",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_prof",
                    "description": "Quantidade de turmas na educação profissional",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_prof_tec",
                    "description": "Quantidade de turmas na educação profissional técnica",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_eja",
                    "description": "Quantidade de turmas na EJA",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_eja_fund",
                    "description": "Quantidade de turmas na EJA: ensino fundamental",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_eja_med",
                    "description": "Quantidade de turmas na EJA: ensino médio",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_esp",
                    "description": "Quantidade de turmas na educação especial",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_esp_cc",
                    "description": "Quantidade de turmas na educação especial: classes comuns",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_esp_ce",
                    "description": "Quantidade de turmas na educação especial: classes especiais",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_bas_d",
                    "description": "Quantidade de turmas na educação básica no turno diurno",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_bas_n",
                    "description": "Quantidade de turmas na educação básica no turno noturno",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_bas_ead",
                    "description": "Quantidade de turmas na educação básica em EAD",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_inf_int",
                    "description": "Quantidade de turmas na educação infantil em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_inf_cre_int",
                    "description": "Quantidade de turmas na creche em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_inf_pre_int",
                    "description": "Quantidade de turmas na pré-escola em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_fund_int",
                    "description": "Quantidade de turmas no ensino fundamental em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_fund_ai_int",
                    "description": "Quantidade de turmas no ensino fundamental anos iniciais em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_fund_af_int",
                    "description": "Quantidade de turmas no ensino fundamental anos finais em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                },
                {
                    "name": "qt_tur_med_int",
                    "description": "Quantidade de turmas no ensino médio em tempo integral",
                    "type": "number",
                    "semantic_group": "quantidade_turmas"
                }
            ]
        },
        {
            "name": "municipio",
            "columns": [
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "nm_mun",
                    "description": "Nome do município",
                    "type": "string"
                },
                {
                    "name": "cd_rgi",
                    "description": "Código da região geográfica imediata",
                    "type": "string"
                },
                {
                    "name": "cd_rgint",
                    "description": "Código da região geográfica intermediária",
                    "type": "string"
                },
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "cd_concu",
                    "description": "Código da concentração urbana",
                    "type": "string"
                },
                {
                    "name": "area_km2",
                    "description": "Área do município em quilômetros quadrados",
                    "type": "number",
                    "min": 0,
                    "max": 160000
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial do município",
                    "type": "string"
                }
            ]
        },
        {
            "name": "pais",
            "columns": [
                {
                    "name": "pais",
                    "description": "Nome do país",
                    "type": "string"
                },
                {
                    "name": "area_km2",
                    "description": "Área do país em quilômetros quadrados",
                    "type": "number",
                    "min": 0,
                    "max": 17100000
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial do país",
                    "type": "string"
                }
            ]
        },
        {
            "name": "regiao",
            "columns": [
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "nm_regia",
                    "description": "Nome da região",
                    "type": "string"
                },
                {
                    "name": "sigla_rg",
                    "description": "Sigla da região",
                    "type": "string"
                },
                {
                    "name": "area_km2",
                    "description": "Área da região em quilômetros quadrados",
                    "type": "number",
                    "min": 0,
                    "max": 4000000
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial da região",
                    "type": "string"
                }
            ]
        },
        {
            "name": "rg_imediata",
            "columns": [
                {
                    "name": "cd_rgi",
                    "description": "Código da região geográfica imediata",
                    "type": "string"
                },
                {
                    "name": "nm_rgi",
                    "description": "Nome da região geográfica imediata",
                    "type": "string"
                },
                {
                    "name": "cd_rgint",
                    "description": "Código da região geográfica intermediária",
                    "type": "string"
                },
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "area_km2",
                    "description": "Área da região geográfica imediata em quilômetros quadrados",
                    "type": "number",
                    "min": 0,
                    "max": 300000
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial da região geográfica imediata",
                    "type": "string"
                }
            ]
        },
        {
            "name": "rg_intermediaria",
            "columns": [
                {
                    "name": "cd_rgint",
                    "description": "Código da região geográfica intermediária",
                    "type": "string"
                },
                {
                    "name": "nm_rgint",
                    "description": "Nome da região geográfica intermediária",
                    "type": "string"
                },
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "area_km2",
                    "description": "Área da região geográfica intermediária em quilômetros quadrados",
                    "type": "number",
                    "min": 0,
                    "max": 1600000
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial da região geográfica intermediária",
                    "type": "string"
                }
            ]
        },
        {
            "name": "setor",
            "columns": [
                {
                    "name": "cd_setor",
                    "description": "Código do setor censitário",
                    "type": "string"
                },
                {
                    "name": "situacao",
                    "description": "Situação do setor censitário",
                    "type": "enum",
                    "value_group_labels": {},
                    "enums": [
                        { "value": "Urbano", "description": "Urbano" },
                        { "value": "Rural", "description": "Rural" }
                    ]
                },
                {
                    "name": "cd_sit",
                    "description": "Código da situação do setor censitário",
                    "type": "string"
                },
                {
                    "name": "cd_tipo",
                    "description": "Código do tipo de setor censitário",
                    "type": "string"
                },
                {
                    "name": "area_km2",
                    "description": "Área do setor censitário em quilômetros quadrados",
                    "type": "number",
                    "min": 0,
                    "max": 100000
                },
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "cd_dist",
                    "description": "Código do distrito",
                    "type": "string"
                },
                {
                    "name": "cd_subdist",
                    "description": "Código do subdistrito",
                    "type": "string"
                },
                {
                    "name": "cd_bairro",
                    "description": "Código do bairro",
                    "type": "string"
                },
                {
                    "name": "nm_bairro",
                    "description": "Nome do bairro",
                    "type": "string"
                },
                {
                    "name": "cd_nu",
                    "description": "Código do núcleo urbano",
                    "type": "string"
                },
                {
                    "name": "nm_nu",
                    "description": "Nome do núcleo urbano",
                    "type": "string"
                },
                {
                    "name": "cd_fcu",
                    "description": "Código da face de unidade",
                    "type": "string"
                },
                {
                    "name": "nm_fcu",
                    "description": "Nome da face de unidade",
                    "type": "string"
                },
                {
                    "name": "cd_aglom",
                    "description": "Código da aglomeração",
                    "type": "string"
                },
                {
                    "name": "nm_aglom",
                    "description": "Nome da aglomeração",
                    "type": "string"
                },
                {
                    "name": "cd_rgint",
                    "description": "Código da região geográfica intermediária",
                    "type": "string"
                },
                {
                    "name": "cd_rgi",
                    "description": "Código da região geográfica imediata",
                    "type": "string"
                },
                {
                    "name": "cd_concurb",
                    "description": "Código da concentração urbana",
                    "type": "string"
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial do setor censitário",
                    "type": "string"
                }
            ]
        },
        {
            "name": "subdistrito",
            "columns": [
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "cd_mun",
                    "description": "Código do município",
                    "type": "string"
                },
                {
                    "name": "cd_dist",
                    "description": "Código do distrito",
                    "type": "string"
                },
                {
                    "name": "cd_subdist",
                    "description": "Código do subdistrito",
                    "type": "string"
                },
                {
                    "name": "nm_subdist",
                    "description": "Nome do subdistrito",
                    "type": "string"
                },
                {
                    "name": "cd_rgint",
                    "description": "Código da região geográfica intermediária",
                    "type": "string"
                },
                {
                    "name": "cd_rgi",
                    "description": "Código da região geográfica imediata",
                    "type": "string"
                },
                {
                    "name": "cd_concurb",
                    "description": "Código da concentração urbana",
                    "type": "string"
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial do subdistrito",
                    "type": "string"
                }
            ]
        },
        {
            "name": "unidade_federativa",
            "columns": [
                {
                    "name": "cd_uf",
                    "description": "Código da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "nm_uf",
                    "description": "Nome da unidade federativa",
                    "type": "string"
                },
                {
                    "name": "sigla_uf",
                    "description": "Sigla da unidade federativa",
                    "type": "enum",
                    "value_group_labels": {
                        "nordeste": "Nordeste",
                        "sul": "Sul",
                        "sudeste": "Sudeste",
                        "norte": "Norte",
                        "centro_oeste": "Centro-Oeste"
                    },
                    "enums": [
                        {
                            "value": "AC",
                            "description": "Acre",
                            "value_group": "norte"
                        },
                        {
                            "value": "AL",
                            "description": "Alagoas",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "AM",
                            "description": "Amazonas",
                            "value_group": "norte"
                        },
                        {
                            "value": "AP",
                            "description": "Amapá",
                            "value_group": "norte"
                        },
                        {
                            "value": "BA",
                            "description": "Bahia",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "CE",
                            "description": "Ceará",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "DF",
                            "description": "Distrito Federal",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "ES",
                            "description": "Espírito Santo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "GO",
                            "description": "Goiás",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MA",
                            "description": "Maranhão",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "MG",
                            "description": "Minas Gerais",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "MS",
                            "description": "Mato Grosso do Sul",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "MT",
                            "description": "Mato Grosso",
                            "value_group": "centro_oeste"
                        },
                        {
                            "value": "PA",
                            "description": "Pará",
                            "value_group": "norte"
                        },
                        {
                            "value": "PB",
                            "description": "Paraíba",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PE",
                            "description": "Pernambuco",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PI",
                            "description": "Piauí",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "PR",
                            "description": "Paraná",
                            "value_group": "sul"
                        },
                        {
                            "value": "RJ",
                            "description": "Rio de Janeiro",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "RN",
                            "description": "Rio Grande do Norte",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "RO",
                            "description": "Rondônia",
                            "value_group": "norte"
                        },
                        {
                            "value": "RR",
                            "description": "Roraima",
                            "value_group": "norte"
                        },
                        {
                            "value": "RS",
                            "description": "Rio Grande do Sul",
                            "value_group": "sul"
                        },
                        {
                            "value": "SC",
                            "description": "Santa Catarina",
                            "value_group": "sul"
                        },
                        {
                            "value": "SE",
                            "description": "Sergipe",
                            "value_group": "nordeste"
                        },
                        {
                            "value": "SP",
                            "description": "São Paulo",
                            "value_group": "sudeste"
                        },
                        {
                            "value": "TO",
                            "description": "Tocantins",
                            "value_group": "norte"
                        }
                    ]
                },
                {
                    "name": "cd_regia",
                    "description": "Código da região",
                    "type": "string"
                },
                {
                    "name": "area_km2",
                    "description": "Área da unidade federativa em quilômetros quadrados",
                    "type": "number",
                    "min": 0,
                    "max": 1600000
                },
                {
                    "name": "geometry",
                    "description": "Geometria espacial da unidade federativa",
                    "type": "string"
                }
            ]
        },
    ],
}
