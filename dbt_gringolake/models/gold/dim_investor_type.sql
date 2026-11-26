with investor_types as (
    select *
    from (
        values
            ('estrangeiro', 'Investidor Estrangeiro', 'ESTRANG', 1, '#22C55E', true),
            ('institucional', 'Institucional', 'INSTIT.', 2, '#93C5FD', true),
            ('pessoa_fisica', 'Pessoa Física', 'P.F.', 3, '#FACC15', true),
            ('instituicoes_financeiras', 'Instituições Financeiras', 'INST. FIN.', 4, '#A855F7', false),
            ('outros', 'Outros', 'OUTROS', 5, '#94A3B8', false)
    ) as t(
        investor_type_code,
        investor_type_name_pt,
        investor_type_short_pt,
        display_order,
        suggested_color_hex,
        is_primary_chart_group
    )
)

select
    investor_type_code,
    investor_type_name_pt,
    investor_type_short_pt,
    display_order,
    suggested_color_hex,
    is_primary_chart_group
from investor_types
order by display_order
