CREATE DATABASE analytics;
\c analytics;

CREATE TABLE IF NOT EXISTS sensor_measurements (
    id SERIAL PRIMARY KEY,
    measurement_id VARCHAR(64) UNIQUE NOT NULL,
    temperature_celsius NUMERIC(5, 2) NOT NULL,
    humidity_percent NUMERIC(5, 2) NOT NULL,
    air_quality_aqi INTEGER,
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sensor_recorded_at ON sensor_measurements(recorded_at);

GRANT ALL PRIVILEGES ON DATABASE analytics TO airflow;
GRANT ALL ON SCHEMA public TO airflow;
GRANT ALL ON ALL TABLES IN SCHEMA public TO airflow;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO airflow;
