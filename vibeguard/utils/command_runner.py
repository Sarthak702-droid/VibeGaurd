import subprocess
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass

@dataclass
class RunResult:
    status: str  # "Passed", "Failed", "Skipped"
    details: str
    command_str: str

ALLOWED_COMMAND_STRINGS = {
    "npm test",
    "npm run lint",
    "npm run typecheck",
    "npm audit",
    "pytest",
    "ruff check .",
    "bandit -r .",
    "pip-audit",
    "python -m compileall .",
}

def is_allowlisted(command: list[str]) -> bool:
    if not command:
        return False
    first = command[0]
    if first == sys.executable or Path(first).name.lower() in ("python", "python.exe", "python3"):
        normalized_first = "python"
    else:
        normalized_first = first
    
    normalized_cmd_str = " ".join([normalized_first] + command[1:])
    return normalized_cmd_str in ALLOWED_COMMAND_STRINGS

def run_project_command(project_path: Path, command: list[str], timeout: int = 120) -> RunResult:
    cmd_str = " ".join(command)
    
    # 1. Allowlist check
    if not is_allowlisted(command):
        return RunResult(
            status="Skipped",
            details="Command is not in the security allowlist.",
            command_str=cmd_str
        )
    
    # 2. Check executable availability using shutil.which (except for sys.executable)
    executable = command[0]
    if executable != sys.executable:
        resolved = shutil.which(executable)
        if not resolved:
            return RunResult(
                status="Skipped",
                details=f"{executable} is not installed or not on PATH.",
                command_str=cmd_str
            )
        # Update command to use the resolved path for subprocess compatibility
        command = [resolved] + command[1:]
    
    # 3. Execute
    try:
        result = subprocess.run(
            command,
            cwd=project_path,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False
        )
    except FileNotFoundError:
        return RunResult(
            status="Skipped",
            details=f"{executable} is not installed or not on PATH.",
            command_str=cmd_str
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            status="Failed",
            details=f"Command timed out after {timeout} seconds.",
            command_str=cmd_str
        )
    
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode == 0:
        return RunResult(
            status="Passed",
            details=output or "Command passed.",
            command_str=cmd_str
        )
    else:
        return RunResult(
            status="Failed",
            details=output or f"Command exited with {result.returncode}.",
            command_str=cmd_str
        )
