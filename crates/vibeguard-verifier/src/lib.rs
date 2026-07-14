//! Explicit verification boundary. Commands use direct arguments and never a shell.

use std::{
    path::Path,
    process::Command,
    thread,
    time::{Duration, Instant},
};
use vibeguard_core::{CheckResult, CheckStatus, Detection};
pub fn verify(
    root: &Path,
    detection: &Detection,
    quick: bool,
    timeout: Duration,
) -> Vec<CheckResult> {
    let mut commands: Vec<(String, Vec<String>)> = Vec::new();
    if detection.languages.iter().any(|item| item == "Rust") {
        commands.push((
            "cargo fmt".to_owned(),
            vec!["cargo".to_owned(), "fmt".to_owned(), "--check".to_owned()],
        ));
        commands.push((
            "cargo test".to_owned(),
            vec!["cargo".to_owned(), "test".to_owned()],
        ));
        if !quick {
            commands.push((
                "cargo clippy".to_owned(),
                vec![
                    "cargo".to_owned(),
                    "clippy".to_owned(),
                    "--all-targets".to_owned(),
                    "--".to_owned(),
                    "-D".to_owned(),
                    "warnings".to_owned(),
                ],
            ));
        }
    }
    if detection.languages.iter().any(|item| item == "Python") {
        commands.push((
            "python compile".to_owned(),
            vec![
                "python".to_owned(),
                "-m".to_owned(),
                "compileall".to_owned(),
                ".".to_owned(),
            ],
        ));
        commands.push((
            "pytest".to_owned(),
            vec!["python".to_owned(), "-m".to_owned(), "pytest".to_owned()],
        ));
    }
    if detection.languages.iter().any(|item| item == "Node.js") {
        commands.push((
            "npm test".to_owned(),
            vec!["npm".to_owned(), "test".to_owned()],
        ));
    }
    commands
        .into_iter()
        .map(|(name, command)| execute(root, name, command, timeout))
        .collect()
}
fn execute(root: &Path, name: String, command: Vec<String>, timeout: Duration) -> CheckResult {
    let started = Instant::now();
    let Some((program, args)) = command.split_first() else {
        return CheckResult {
            name,
            status: CheckStatus::Skipped,
            details: "empty command".to_owned(),
            command,
            exit_code: None,
            duration_ms: 0,
        };
    };
    let mut child = match Command::new(program).args(args).current_dir(root).spawn() {
        Ok(child) => child,
        Err(error) => {
            return CheckResult {
                name,
                status: CheckStatus::Skipped,
                details: format!("tool unavailable: {error}"),
                command,
                exit_code: None,
                duration_ms: started.elapsed().as_millis(),
            };
        }
    };
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                return CheckResult {
                    name,
                    status: if status.success() {
                        CheckStatus::Passed
                    } else {
                        CheckStatus::Failed
                    },
                    details: format!(
                        "exit status {}",
                        status
                            .code()
                            .map_or_else(|| "signal".to_owned(), |code| code.to_string())
                    ),
                    command,
                    exit_code: status.code(),
                    duration_ms: started.elapsed().as_millis(),
                };
            }
            Ok(None) if started.elapsed() <= timeout => thread::sleep(Duration::from_millis(25)),
            Ok(None) => {
                let _ = child.kill();
                let _ = child.wait();
                return CheckResult {
                    name,
                    status: CheckStatus::TimedOut,
                    details: "verification command timed out".to_owned(),
                    command,
                    exit_code: None,
                    duration_ms: started.elapsed().as_millis(),
                };
            }
            Err(error) => {
                return CheckResult {
                    name,
                    status: CheckStatus::Failed,
                    details: format!("process error: {error}"),
                    command,
                    exit_code: None,
                    duration_ms: started.elapsed().as_millis(),
                };
            }
        }
    }
}
