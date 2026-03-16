{{ config(
    materialized='table',
    schema='SILVER',
    tags=['silver', 'tmdb', 'movie', 'genre']
) }}

with source as (
    select * from {{ ref('base_bronze_TMDB_MOVIE_RAW') }}
),

exploded as (
    select
        RAW_JSON:id::INTEGER as MOVIE_ID,
        g.value::INTEGER     as GENRE_ID,
        INGESTED_AT
    from source,
    lateral flatten(input => RAW_JSON:genre_ids) g
    qualify row_number() over (partition by RAW_JSON:id::INTEGER, g.value::INTEGER order by INGESTED_AT desc) = 1
)

select
    MOVIE_ID,
    GENRE_ID
from exploded
