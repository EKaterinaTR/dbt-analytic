-- ODS: measurements — только валидные (sensor_id не пустой, recorded_at не в будущем)
{{ config(
    schema='ods',
    tags=['ods'],
    alias='ods_measurements',
) }}

select
    measurement_pk,
    measurement_id,
    sensor_id,
    temperature_celsius,
    humidity_percent,
    air_quality_aqi,
    recorded_at,
    recorded_date,
    created_at
from {{ ref('stg_measurements') }}
where sensor_id is not null
  and sensor_id != ''
  and recorded_at <= current_timestamp
