"""Vendor-neutral coding-agent registry and guarded subprocess runner."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from vibeguard.core.report_generator import ensure_vibeguard_dir
from vibeguard.snapshot import capture_snapshot, compare_snapshot, save_snapshot


@dataclass(frozen=True)
class AgentAdapter:
    name: str
    executable: str
    display_name: str
    non_interactive_args: tuple[str, ...] = ()
    interactive: bool = True

    def resolve(self) -> str | None:
        return shutil.which(self.executable)

    def is_installed(self) -> bool:
        return self.resolve() is not None

    def get_version(self) -> str | None:
        resolved = self.resolve()
        if not resolved:
            return None
        try:
            result = subprocess.run([resolved, "--version"], text=True, capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        value = (result.stdout or result.stderr).strip().splitlines()
        return value[0][:200] if value else None

    def build_command(self, task: str | None = None, extra_args: list[str] | None = None) -> list[str]:
        resolved = self.resolve()
        if not resolved:
            raise FileNotFoundError(f"{self.display_name} executable '{self.executable}' was not found.")
        command = [resolved]
        if task:
            if not self.non_interactive_args:
                raise ValueError(f"{self.display_name} does not declare a safe non-interactive task mode.")
            command.extend(self.non_interactive_args)
            command.append(task)
        command.extend(extra_args or [])
        return command


ADAPTERS: dict[str, AgentAdapter] = {
    "codex": AgentAdapter("codex", "codex", "OpenAI Codex", ("exec",)),
    "antigravity": AgentAdapter("antigravity", "antigravity", "Antigravity CLI", ("chat",)),
}


def get_agent(name: str) -> AgentAdapter:
    try:
        return ADAPTERS[name.lower()]
    except KeyError as exc:
        supported = ", ".join(sorted(ADAPTERS))
        raise ValueError(f"Unknown agent '{name}'. Supported agents: {supported}") from exc


@dataclass(frozen=True)
class AgentSession:
    session_id: str
    agent: str
    task: str | None
    start_time: str
    end_time: str
    exit_code: int
    baseline_commit: str | None
    files_changed: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    verification_status: str = "not_run"
    risk_score: int = 0


def run_agent(
    root: Path,
    adapter: AgentAdapter,
    *,
    task: str | None = None,
    extra_args: list[str] | None = None,
    timeout: int | None = None,
) -> AgentSession:
    root = root.resolve()
    command = adapter.build_command(task, extra_args)
    baseline = capture_snapshot(root, agent=adapter.name, task=task)
    save_snapshot(root, baseline)
    started = datetime.now(UTC)
    process = subprocess.Popen(command, cwd=root, start_new_session=os.name != "nt")
    try:
        exit_code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        exit_code = 124
    except KeyboardInterrupt:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGINT)
        else:
            process.send_signal(getattr(signal, "CTRL_BREAK_EVENT", signal.SIGINT))
        exit_code = process.wait()
    changes = compare_snapshot(root, baseline)
    session = AgentSession(
        session_id=str(uuid.uuid4()),
        agent=adapter.name,
        task=task,
        start_time=started.isoformat(),
        end_time=datetime.now(UTC).isoformat(),
        exit_code=exit_code,
        baseline_commit=baseline.commit,
        files_changed=changes.files,
        command=[adapter.executable, *command[1:]],
    )
    directory = ensure_vibeguard_dir(root) / "sessions"
    directory.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(session), indent=2)
    (directory / f"{session.session_id}.json").write_text(payload, encoding="utf-8")
    (directory / "latest.json").write_text(payload, encoding="utf-8")
    return session
