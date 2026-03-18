{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold', 'tmdb', 'credits']
) }}

with cast_persons as (
    select PERSON_ID, NAME from {{ ref('silver_movie_cast') }}
),
crew_persons as (
    select PERSON_ID, NAME from {{ ref('silver_movie_crew') }}
),
all_persons as (
    select PERSON_ID, NAME from cast_persons
    union
    select PERSON_ID, NAME from crew_persons
),
deduplicated as (
    select
        PERSON_ID,
        NAME
    from all_persons
    qualify row_number() over (partition by PERSON_ID order by NAME) = 1
)
select * from deduplicated
