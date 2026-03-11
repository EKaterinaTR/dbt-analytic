-- Staging: sensors — приведение типов, переименование не требуется
-- Схема: staging (тег stg)
{{ config(
    schema='staging',
    tags=['stg'],
    alias='stg_sensors',
) }}

select
    id as sensor_pk,
    sensor_id,
    name,
    location_code,
    installed_at::timestamptz as installed_at,
    created_at::timestamptz as created_at
from {{ source('raw', 'sensors') }}
