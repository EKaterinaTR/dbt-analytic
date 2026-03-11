-- Mart: свежие алерты за последние N дней — incremental INSERT+DELETE
-- Стратегия: pre_hook удаляет алерты старше retention_days; затем append только новых по created_at
{{ config(
    materialized='incremental',
    schema='marts',
    tags=['dm'],
    alias='dm_alerts_recent',
    incremental_strategy='append',
    pre_hook="{% if is_incremental() %}DELETE FROM {{ this }} WHERE created_at < current_timestamp - interval '" ~ var('alert_retention_days', 30) ~ " days'{% else %}SELECT 1{% endif %}",
) }}

select
    a.alert_id,
    a.measurement_id,
    a.severity,
    a.created_at,
    m.sensor_id,
    m.recorded_at as measurement_recorded_at
from {{ ref('stg_alerts') }} a
left join {{ ref('stg_measurements') }} m on m.measurement_id = a.measurement_id
{% if is_incremental() %}
where a.created_at >= current_timestamp - interval '{{ var("alert_retention_days", 30) }} days'
  and a.created_at > (select coalesce(max(created_at), '1900-01-01'::timestamptz) from {{ this }})
{% endif %}
