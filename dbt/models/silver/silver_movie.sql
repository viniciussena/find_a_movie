{{ config(
    materialized='table',
    schema='SILVER',
    tags=['silver', 'tmdb', 'movie']
) }}

with source as (
    select * from {{ ref('base_bronze_TMDB_MOVIE_RAW') }}
),

deduplicated as (
    select
        RAW_JSON:id::INTEGER            as MOVIE_ID,
        RAW_JSON:title::VARCHAR         as TITLE,
        RAW_JSON:original_title::VARCHAR as ORIGINAL_TITLE,
        RAW_JSON:original_language::VARCHAR as ORIGINAL_LANGUAGE,
        RAW_JSON:overview::VARCHAR      as OVERVIEW,
        NULLIF(RAW_JSON:release_date::VARCHAR, '')::DATE as RELEASE_DATE,
        RAW_JSON:popularity::FLOAT      as POPULARITY,
        RAW_JSON:vote_average::FLOAT    as VOTE_AVERAGE,
        RAW_JSON:vote_count::INTEGER    as VOTE_COUNT,
        RAW_JSON:adult::BOOLEAN         as ADULT,
        ENDPOINT,
        INGESTED_AT
    from source
    qualify row_number() over (partition by RAW_JSON:id::INTEGER order by INGESTED_AT desc) = 1
)

select * from deduplicated
