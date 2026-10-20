from pathlib import Path

from app.config import BACKEND_ENV_FILE, Settings


def test_backend_dotenv_path_is_absolute_and_anchored_to_backend(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    assert BACKEND_ENV_FILE.is_absolute()
    assert BACKEND_ENV_FILE == Path(__file__).resolve().parents[1] / ".env"
    assert Settings.model_config["env_file"] == BACKEND_ENV_FILE


def test_settings_load_values_from_dotenv_and_environment_overrides(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "AWS_MOCK_MODE=false\nAWS_REGION=ap-south-1\nAWS_PROFILE=project\n",
        encoding="utf-8",
    )
    for key in ("AWS_MOCK_MODE", "AWS_REGION", "AWS_PROFILE"):
        monkeypatch.delenv(key, raising=False)

    loaded = Settings(_env_file=dotenv)
    assert loaded.AWS_MOCK_MODE is False
    assert loaded.AWS_REGION == "ap-south-1"
    assert loaded.AWS_PROFILE == "project"

    # Pydantic's normal precedence is intentional: explicit process
    # environment overrides the dotenv file and should be set deliberately.
    monkeypatch.setenv("AWS_MOCK_MODE", "true")
    overridden = Settings(_env_file=dotenv)
    assert overridden.AWS_MOCK_MODE is True
