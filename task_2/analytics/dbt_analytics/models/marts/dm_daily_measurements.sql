-- Mart: дневные агрегаты по датчику — incremental MERGE по (recorded_date, sensor_id)
-- Стратегия: merge (PostgreSQL 15), unique_key = (recorded_date, sensor_id)
{{ config(
    materialized='incremental',
    schema='marts',
    tags=['dm'],
    alias='dm_daily_measurements',
    unique_key=['recorded_date', 'sensor_id'],
    incremental_strategy='merge',
) }}

with src as (
    select
        recorded_date,
        sensor_id,
        count(*) as measurement_count,
        avg(temperature_celsius) as avg_temperature_celsius,
        avg(humidity_percent) as avg_humidity_percent,
        avg(air_quality_aqi) as avg_air_quality_aqi,
        max(recorded_at) as last_recorded_at
    from {{ ref('ods_measurements') }}
    {% if is_incremental() %}
    where recorded_date >= (select coalesce(max(recorded_date), '1900-01-01'::date) from {{ this }})
    {% endif %}
    group by recorded_date, sensor_id
)
select
    recorded_date,
    sensor_id,
    measurement_count,
    round(avg_temperature_celsius::numeric, 2) as avg_temperature_celsius,
    round(avg_humidity_percent::numeric, 2) as avg_humidity_percent,
    round(avg_air_quality_aqi::numeric, 2) as avg_air_quality_aqi,
    last_recorded_at
from src
