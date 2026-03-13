-- Staging: sensors — приведение типов.
-- Справочник дополняется датчиками из измерений, которых ещё нет в raw.sensors (обновление справочника).
-- Схема: staging (тег stg)
{{ config(
    schema='staging',
    tags=['stg'],
    alias='stg_sensors',
) }}

with sensors_raw as (
    select
        id as sensor_pk,
        sensor_id,
        name,
        location_code,
        installed_at::timestamptz as installed_at,
        created_at::timestamptz as created_at
    from {{ source('raw', 'sensors') }}
),
sensor_ids_from_measurements as (
    select distinct m.sensor_id
    from {{ source('raw', 'sensor_measurements') }} m
    left join {{ source('raw', 'sensors') }} s on s.sensor_id = m.sensor_id
    where s.sensor_id is null
      and m.sensor_id is not null
      and m.sensor_id != ''
),
supplement as (
    select
        -row_number() over (order by sensor_id) as sensor_pk,
        sensor_id,
        cast(null as text) as name,
        cast(null as text) as location_code,
        cast(null as timestamptz) as installed_at,
        cast(null as timestamptz) as created_at
    from sensor_ids_from_measurements
)
select * from sensors_raw
union all
select * from supplement
