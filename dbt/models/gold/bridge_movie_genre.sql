{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'movie', 'genre']
) }}

with source as (
    select * from {{ ref('silver_bridge_movie_genre') }}
)

select
    MOVIE_ID,
    GENRE_ID
from source
