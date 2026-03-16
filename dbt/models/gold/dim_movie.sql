{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'movie']
) }}

with source as (
    select * from {{ ref('silver_movie') }}
)

select
    MOVIE_ID,
    TITLE,
    ORIGINAL_TITLE,
    ORIGINAL_LANGUAGE,
    OVERVIEW,
    RELEASE_DATE,
    POPULARITY,
    VOTE_AVERAGE,
    VOTE_COUNT,
    ADULT
from source
