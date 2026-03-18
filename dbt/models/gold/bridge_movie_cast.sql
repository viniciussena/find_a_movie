{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'credits']
) }}

with source as (
    select * from {{ ref('silver_movie_cast') }}
)
select
    MOVIE_ID,
    PERSON_ID,
    CHARACTER,
    CAST_ORDER
from source
