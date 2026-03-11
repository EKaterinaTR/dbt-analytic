-- Кастомный тест: severity только допустимые значения (low, medium, high)
select
    alert_id,
    severity
from {{ ref('stg_alerts') }}
where severity not in ('low', 'medium', 'high')
