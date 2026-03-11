-- Кастомный тест: recorded_at не в будущем (ODS уже фильтрует, этот тест на stg)
select
    measurement_id,
    recorded_at
from {{ ref('stg_measurements') }}
where recorded_at > current_timestamp
