"""Typed project/global configuration with environment overrides."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ProjectConfig(BaseModel):
    name: str = "project"


class IntelligenceConfig(BaseModel):
    provider: str = "glm"
    model: str = "z-ai/glm-5.2"
    local_only: bool = True
    timeout: int = Field(default=60, ge=1, le=600)


class AgentsConfig(BaseModel):
    default: str = "codex"
    timeout: int | None = Field(default=None, ge=1)


class PoliciesConfig(BaseModel):
    risk_level: str = "standard"
    block_protected_files: bool = True
    blocking_score: int = Field(default=80, ge=0, le=100)


class VerificationConfig(BaseModel):
    timeout: int = Field(default=300, ge=1, le=3600)
    custom_commands: list[list[str]] = Field(default_factory=list)


class VibeGuardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    intelligence: IntelligenceConfig = Field(default_factory=IntelligenceConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    policies: PoliciesConfig = Field(default_factory=PoliciesConfig)
    protected_paths: list[str] = Field(
        default_factory=lambda: [".env", ".env.*", ".github/workflows/", "migrations/", "auth/"]
    )
    ignore: list[str] = Field(default_factory=list)
    verification: VerificationConfig = Field(default_factory=VerificationConfig)


def default_config(project: Path) -> VibeGuardConfig:
    return VibeGuardConfig(project=ProjectConfig(name=project.resolve().name))


def global_config_path() -> Path:
    override = os.getenv("VIBEGUARD_CONFIG_HOME")
    base = Path(override).expanduser() if override else Path.home() / ".config" / "vibeguard"
    return base / "config.yml"


def project_config_path(project: Path) -> Path:
    root = project.resolve()
    canonical = root / ".vibeguard.yml"
    if canonical.exists():
        return canonical
    legacy = root / ".vibeguard" / "config.yaml"
    return legacy if legacy.exists() else canonical


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Configuration must be a YAML mapping: {path}")
    return value


def _deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _legacy_to_v1(data: dict[str, Any], project: Path) -> dict[str, Any]:
    if "project_name" not in data and "protected_files" not in data:
        return data
    return {
        "version": 1,
        "project": {"name": data.get("project_name", project.resolve().name)},
        "protected_paths": data.get("protected_files", []),
        "ignore": data.get("ignore", []),
    }


def load_config(project: Path) -> VibeGuardConfig:
    data = default_config(project).model_dump()
    data = _deep_merge(data, _read_yaml(global_config_path()))
    data = _deep_merge(data, _legacy_to_v1(_read_yaml(project_config_path(project)), project))
    if provider := os.getenv("VIBEGUARD_INTELLIGENCE_PROVIDER"):
        data["intelligence"]["provider"] = provider
    if model := os.getenv("VIBEGUARD_INTELLIGENCE_MODEL"):
        data["intelligence"]["model"] = model
    if local := os.getenv("VIBEGUARD_LOCAL_ONLY"):
        data["intelligence"]["local_only"] = local.lower() in {"1", "true", "yes", "on"}
    if agent := os.getenv("VIBEGUARD_DEFAULT_AGENT"):
        data["agents"]["default"] = agent
    return VibeGuardConfig.model_validate(data)


def write_project_config(project: Path, config: VibeGuardConfig, *, overwrite: bool = False) -> Path:
    path = project.resolve() / ".vibeguard.yml"
    if path.exists() and not overwrite:
        return path
    path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")
    return path


def set_config_value(project: Path, dotted_key: str, raw_value: str) -> VibeGuardConfig:
    path = project.resolve() / ".vibeguard.yml"
    data = _read_yaml(path) if path.exists() else default_config(project).model_dump()
    parts = dotted_key.split(".")
    if not parts or any(not part for part in parts):
        raise ValueError("Configuration key must use dotted notation.")
    target: dict[str, Any] = data
    for part in parts[:-1]:
        value = target.setdefault(part, {})
        if not isinstance(value, dict):
            raise ValueError(f"Cannot set child key beneath non-mapping '{part}'.")
        target = value
    target[parts[-1]] = yaml.safe_load(raw_value)
    config = VibeGuardConfig.model_validate(data)
    write_project_config(project, config, overwrite=True)
    return config


__all__ = [
    "ValidationError",
    "VibeGuardConfig",
    "default_config",
    "global_config_path",
    "load_config",
    "project_config_path",
    "set_config_value",
    "write_project_config",
]
