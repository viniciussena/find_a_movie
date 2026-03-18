with source as (
        select * from {{ source('bronze', 'TMDB_MOVIE_CREDITS_RAW') }}
  ),
  renamed as (
      select
          {{ adapter.quote("MOVIE_ID") }},
          {{ adapter.quote("ENDPOINT") }},
          {{ adapter.quote("RAW_JSON") }},
          {{ adapter.quote("INGESTED_AT") }}

      from source
  )
  select * from renamed
