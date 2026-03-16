{{ config(
    materialized='table',
    schema='SILVER',
    tags=['silver', 'tmdb', 'genre']
) }}

with source as (
    select * from {{ ref('base_bronze_TMDB_GENRE_RAW') }}
),

with_name as (
    select
        s.GENRE_ID,
        f.value:name::VARCHAR as GENRE_NAME,
        s.ENDPOINT,
        s.INGESTED_AT
    from source s,
    lateral flatten(input => s.RAW_JSON:genres) f
    where f.value:id::INTEGER = s.GENRE_ID
),

deduplicated as (
    select
        GENRE_ID,
        GENRE_NAME,
        ENDPOINT,
        INGESTED_AT
    from with_name
    qualify row_number() over (partition by GENRE_ID order by INGESTED_AT desc) = 1
)

select * from deduplicated
