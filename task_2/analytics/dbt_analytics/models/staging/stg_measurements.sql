-- Staging: measurements — приведение типов, date для витрин
-- Схема: staging (тег stg)
{{ config(
    schema='staging',
    tags=['stg'],
    alias='stg_measurements',
) }}

select
    id as measurement_pk,
    measurement_id,
    sensor_id,
    temperature_celsius,
    humidity_percent,
    air_quality_aqi,
    recorded_at::timestamptz as recorded_at,
    date(recorded_at::timestamptz) as recorded_date,
    created_at::timestamptz as created_at
from {{ source('raw', 'sensor_measurements') }}
