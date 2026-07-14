//! Safe adapters for known agent CLIs.

use std::{path::Path, process::Command};
use vibeguard_core::VibeGuardError;
pub trait AgentAdapter {
    fn name(&self) -> &'static str;
    fn executable(&self) -> &'static str;
    fn task_args(&self, task: &str) -> Result<Vec<String>, VibeGuardError>;
}
pub struct Codex;
impl AgentAdapter for Codex {
    fn name(&self) -> &'static str {
        "codex"
    }
    fn executable(&self) -> &'static str {
        "codex"
    }
    fn task_args(&self, task: &str) -> Result<Vec<String>, VibeGuardError> {
        Ok(vec!["exec".to_owned(), task.to_owned()])
    }
}
pub struct Claude;
impl AgentAdapter for Claude {
    fn name(&self) -> &'static str {
        "claude"
    }
    fn executable(&self) -> &'static str {
        "claude"
    }
    fn task_args(&self, task: &str) -> Result<Vec<String>, VibeGuardError> {
        Ok(vec!["-p".to_owned(), task.to_owned()])
    }
}
pub fn adapter(name: &str) -> Result<Box<dyn AgentAdapter>, VibeGuardError> {
    match name {
        "codex" => Ok(Box::new(Codex)),
        "claude" => Ok(Box::new(Claude)),
        _ => Err(VibeGuardError::InvalidInput(format!(
            "unknown agent '{name}'; supported: codex, claude"
        ))),
    }
}
pub fn run(root: &Path, adapter: &dyn AgentAdapter, task: &str) -> Result<i32, VibeGuardError> {
    let args = adapter.task_args(task)?;
    let status = Command::new(adapter.executable())
        .args(args)
        .current_dir(root)
        .status()
        .map_err(|error| {
            VibeGuardError::Unsupported(format!("{} is unavailable: {error}", adapter.executable()))
        })?;
    Ok(status.code().unwrap_or(1))
}
