-- Staging: alerts — приведение типов
-- Схема: staging (тег stg)
{{ config(
    schema='staging',
    tags=['stg'],
    alias='stg_alerts',
) }}

select
    id as alert_pk,
    alert_id,
    measurement_id,
    severity,
    created_at::timestamptz as created_at,
    loaded_at::timestamptz as loaded_at
from {{ source('raw', 'alerts') }}
