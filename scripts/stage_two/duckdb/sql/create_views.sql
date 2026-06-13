-- DuckDB views over Stage Two Parquet artifacts.
-- Replace ${PATH_DATA_STORAGE} before execution when using this script directly.

CREATE OR REPLACE VIEW normalized_all AS
SELECT *
FROM read_parquet('${PATH_DATA_STORAGE}/parquet/normalized/**/*.parquet', union_by_name = true);

CREATE OR REPLACE VIEW features_all AS
SELECT *
FROM read_parquet('${PATH_DATA_STORAGE}/parquet/features/**/*.parquet', union_by_name = true);

CREATE OR REPLACE VIEW model_ready_all AS
SELECT *
FROM read_parquet('${PATH_DATA_STORAGE}/parquet/model_ready/**/*.parquet', union_by_name = true);
