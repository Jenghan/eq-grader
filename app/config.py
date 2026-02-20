from pathlib import Path
from dataclasses import dataclass, field
import yaml


@dataclass
class Settings:
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"
    database_url: str = "sqlite:///./eq_grader.db"
    questionnaires_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "questionnaires")
    questionnaires: dict = field(default_factory=dict)

    def load_questionnaires(self) -> None:
        self.questionnaires = {}
        for yaml_file in self.questionnaires_dir.glob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                self.questionnaires[config["id"]] = config


settings = Settings()
