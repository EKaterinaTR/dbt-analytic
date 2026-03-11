-- ODS: sensors — очистка (приведение installed_at)
{{ config(
    schema='ods',
    tags=['ods'],
    alias='ods_sensors',
) }}

select
    sensor_pk,
    sensor_id,
    coalesce(nullif(trim(name), ''), 'Unknown') as name,
    coalesce(nullif(trim(location_code), ''), 'N/A') as location_code,
    installed_at,
    created_at
from {{ ref('stg_sensors') }}
where sensor_id is not null and sensor_id != ''
