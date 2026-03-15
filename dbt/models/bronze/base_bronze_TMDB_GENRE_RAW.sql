with source as (
        select * from {{ source('bronze', 'TMDB_GENRE_RAW') }}
  ),
  renamed as (
      select
          {{ adapter.quote("GENRE_ID") }},
        {{ adapter.quote("GENRE_NAME") }},
        {{ adapter.quote("ENDPOINT") }},
        {{ adapter.quote("RAW_JSON") }},
        {{ adapter.quote("INGESTED_AT") }}

      from source
  )
  select * from renamed
    