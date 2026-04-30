from augmentor import create_random_variation
from curseduca_schema import curseduca_schema

original_sqls = [
    """
SELECT 
b.cd_bib,
b.nm_bib,
m.cd_mun,
m.nm_mun,
m.area_km2
FROM public.municipio m
LEFT JOIN public.biblioteca b
ON ST_Intersects(m.geometry, b.geometry)
WHERE m.area_km2 > 10000
AND b.cd_bib IS NOT NULL
AND (b.cep IS NULL OR b.cep = '');
    """,
"""
SELECT
uf.sigla_uf,
COUNT(e.cd_entidade) AS qt_escolas_chuveiro
FROM public.pais p
INNER JOIN public.unidade_federativa uf
ON p.pais = 'Brasil' AND ST_Intersects(uf.geometry, p.geometry)
JOIN public.municipio m
ON m.cd_uf = uf.cd_uf AND ST_Intersects(m.geometry, uf.geometry)
JOIN public.escola e
ON ST_Intersects(m.geometry, e.geometry)
JOIN public.microdados_ed_basica meb
ON meb.cd_entidade = e.cd_entidade AND meb.in_banheiro_chuveiro = 1
WHERE uf.sigla_uf IN ('RR','AC','AM','RO','MT','MS','PR','SC','RS','AP','PA')
AND ST_DWithin(
e.geometry::geography,
ST_Boundary(p.geometry)::geography,
10000
)
GROUP BY uf.sigla_uf
ORDER BY uf.sigla_uf;
"""
]

original_querys = [
    "Quais bibliotecas com CEP ausente estão em municípios com área > 10.000 km2?",
    "Nos estados de fronteira internacional, quantas escolas com banheiro com chuveiro ficam até 10 km da fronteira, por UF?"
]

if __name__ == "__main__":
    for i in range(len(original_querys)):
        print(" = = = = = = = = = = = = = = = =")
        original_query = original_querys[i]
        original_sql = original_sqls[i]
        (new_query, new_sql) = create_random_variation(
            curseduca_schema, original_query, original_sql
        )

        print("============= ORIGINAL ================")
        print("Pergunta original:", original_query)
        print("SQL original:\n")
        print(original_sql)
        print("========== MODIFICADO ===============")
        print("Pergunta modificada:", new_query)
        print("Novo SQL:\n")
        print(new_sql)
