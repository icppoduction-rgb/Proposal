from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.database.duckdb_service import (
    DuckDBDockerConfig,
    DuckDBServiceError,
    build_compose_command,
    build_duckdb_config,
    compose_environment,
    start_duckdb,
    validate_database_name,
)


class DuckDBServiceTests(unittest.TestCase):
    def test_compose_file_uses_official_duckdb_image(self) -> None:
        compose_file = Path(__file__).resolve().parents[1] / "databases" / "duckdb" / "docker-compose.yml"

        content = compose_file.read_text(encoding="utf-8")

        self.assertIn("image: duckdb/duckdb:latest", content)
        self.assertNotIn("datacatering/duckdb:latest", content)

    def test_relative_data_path_is_resolved_from_project_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose_file = root / "databases" / "duckdb" / "docker-compose.yml"
            env_file = root / ".env"
            compose_file.parent.mkdir(parents=True)
            compose_file.write_text("services: {}\n", encoding="utf-8")
            env_file.write_text("DUCKDB_DATABASE=proposal.duckdb\n", encoding="utf-8")

            config = build_duckdb_config(
                project_root=root,
                data_path_value="databases/data/duckdb",
                database="proposal.duckdb",
                compose_file=compose_file,
                env_file=env_file,
            )

        self.assertEqual(config.data_path, (root / "databases" / "data" / "duckdb").resolve())

    def test_database_name_rejects_paths(self) -> None:
        with self.assertRaises(DuckDBServiceError):
            validate_database_name("../proposal.duckdb")

    def test_compose_command_uses_explicit_env_and_compose_files(self) -> None:
        config = DuckDBDockerConfig(
            project_root=Path("C:/project"),
            compose_file=Path("C:/project/databases/duckdb/docker-compose.yml"),
            env_file=Path("C:/project/.env"),
            data_path=Path("C:/project/databases/data/duckdb"),
            database="proposal.duckdb",
        )

        with patch("scripts.database.duckdb_service.detect_compose_command", return_value=["docker", "compose"]):
            command = build_compose_command(config, ["up", "-d"])

        self.assertEqual(
            command,
            [
                "docker",
                "compose",
                "--env-file",
                str(config.env_file),
                "-f",
                str(config.compose_file),
                "up",
                "-d",
            ],
        )

    def test_compose_environment_overrides_data_path_with_absolute_value(self) -> None:
        config = DuckDBDockerConfig(
            project_root=Path("C:/project"),
            compose_file=Path("C:/project/databases/duckdb/docker-compose.yml"),
            env_file=Path("C:/project/.env"),
            data_path=Path("C:/project/databases/data/duckdb"),
            database="proposal.duckdb",
        )

        env = compose_environment(config, {"DUCKDB_DATA_PATH": "relative", "OTHER": "value"})

        self.assertEqual(env["DUCKDB_DATA_PATH"], str(config.data_path))
        self.assertEqual(env["DUCKDB_DATABASE"], "proposal.duckdb")
        self.assertEqual(env["OTHER"], "value")

    def test_start_creates_data_directory_before_compose_up(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = DuckDBDockerConfig(
                project_root=root,
                compose_file=root / "databases" / "duckdb" / "docker-compose.yml",
                env_file=root / ".env",
                data_path=root / "databases" / "data" / "duckdb",
                database="proposal.duckdb",
            )

            with patch("scripts.database.duckdb_service.run_duckdb_compose") as run_compose:
                start_duckdb(config)

            self.assertTrue(config.data_path.is_dir())
            run_compose.assert_called_once_with(config, ["up", "-d"])


if __name__ == "__main__":
    unittest.main()
