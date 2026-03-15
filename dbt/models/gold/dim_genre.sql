{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'genre']
) }}

with source as (
    select * from {{ ref('silver_genre') }}
)

select
    GENRE_ID,
    GENRE_NAME
from source