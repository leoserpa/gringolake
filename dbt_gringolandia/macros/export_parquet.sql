{% macro export_layer_parquet(layer_name) -%}
{%- if execute and flags.WHICH in ('run', 'build') -%}
{%- set data_dir = env_var('GRINGOLANDIA_DATA_DIR', '../data') -%}
COPY (SELECT * FROM {{ this }})
TO '{{ data_dir }}/{{ layer_name }}/{{ this.name }}.parquet'
(FORMAT PARQUET, COMPRESSION ZSTD)
{%- endif -%}
{%- endmacro %}
