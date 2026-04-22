{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'genre', 'movie']
) }}

with bridge as (
    select * from {{ ref('bridge_movie_genre') }}
),

genres as (
    select * from {{ ref('dim_genre') }}
)

select
    g.GENRE_ID,
    g.GENRE_NAME,
    g.GENRE_NAME_CLEAN,
    count(b.MOVIE_ID) as TOTAL_MOVIES
from genres g
left join bridge b on g.GENRE_ID = b.GENRE_ID
group by g.GENRE_ID, g.GENRE_NAME, g.GENRE_NAME_CLEAN
