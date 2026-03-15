{{ config(
    materialized='table',
    schema='SILVER',
    tags=['silver', 'tmdb', 'genre']
) }}

with source as (
    select * from {{ ref('base_bronze_TMDB_GENRE_RAW') }}
),

deduplicated as (
    select
        GENRE_ID,
        GENRE_NAME,
        ENDPOINT,
        INGESTED_AT
    from source
    qualify row_number() over (partition by GENRE_ID order by INGESTED_AT desc) = 1
)

select * from deduplicated