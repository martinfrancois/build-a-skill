from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    port: int
    log_level: str
    database_url: str
    workers: int


def load_settings(env: dict[str, str]) -> Settings:
    """Build the settings listed under Configuration in README.md from the environment."""
    raise NotImplementedError
