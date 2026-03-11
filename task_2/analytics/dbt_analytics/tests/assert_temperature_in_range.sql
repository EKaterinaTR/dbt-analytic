-- Кастомный тест: температура в допустимом диапазоне (например 18–35 для ODS)
-- Возвращает строки, нарушающие условие — тест провален, если есть строки.
select
    measurement_id,
    temperature_celsius
from {{ ref('ods_measurements') }}
where temperature_celsius < 18 or temperature_celsius > 35
