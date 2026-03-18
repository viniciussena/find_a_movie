{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'movie']
) }}

with discover as (
    select * from {{ ref('silver_movie') }}
),
details as (
    select * from {{ ref('silver_movie_details') }}
)

select
    discover.MOVIE_ID,
    COALESCE(details.TITLE, discover.TITLE)                         as TITLE,
    discover.ORIGINAL_TITLE,
    COALESCE(details.ORIGINAL_LANGUAGE, discover.ORIGINAL_LANGUAGE) as ORIGINAL_LANGUAGE,
    COALESCE(details.OVERVIEW, discover.OVERVIEW)                   as OVERVIEW,
    COALESCE(details.RELEASE_DATE, discover.RELEASE_DATE)           as RELEASE_DATE,
    COALESCE(details.POPULARITY, discover.POPULARITY)               as POPULARITY,
    COALESCE(details.VOTE_AVERAGE, discover.VOTE_AVERAGE)           as VOTE_AVERAGE,
    COALESCE(details.VOTE_COUNT, discover.VOTE_COUNT)               as VOTE_COUNT,
    COALESCE(details.ADULT, discover.ADULT)                         as ADULT,
    details.IMDB_ID,
    details.TAGLINE,
    details.STATUS,
    details.RUNTIME,
    details.BUDGET,
    details.REVENUE
from discover
left join details on discover.MOVIE_ID = details.MOVIE_ID
