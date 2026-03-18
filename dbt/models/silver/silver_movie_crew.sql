{{ config(
    materialized='table',
    schema='SILVER',
    tags=['silver', 'tmdb', 'credits']
) }}

with source as (
    select * from {{ ref('base_bronze_TMDB_MOVIE_CREDITS_RAW') }}
),
exploded as (
    select
        RAW_JSON:id::INTEGER      as MOVIE_ID,
        c.value:id::INTEGER       as PERSON_ID,
        c.value:name::VARCHAR     as NAME,
        c.value:job::VARCHAR      as JOB,
        c.value:department::VARCHAR as DEPARTMENT,
        INGESTED_AT
    from source,
    lateral flatten(input => RAW_JSON:crew) c
    qualify row_number() over (partition by RAW_JSON:id::INTEGER, c.value:id::INTEGER, c.value:job::VARCHAR order by INGESTED_AT desc) = 1
)
select
    MOVIE_ID,
    PERSON_ID,
    NAME,
    JOB,
    DEPARTMENT
from exploded
