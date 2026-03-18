{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'credits']
) }}

with source as (
    select * from {{ ref('silver_movie_crew') }}
)
select
    MOVIE_ID,
    PERSON_ID,
    JOB,
    DEPARTMENT
from source
