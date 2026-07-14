//! Safe system-Git transport. It never invokes a shell or repository hooks.

use std::{
    io,
    path::Path,
    process::{Command, Output},
    thread,
    time::{Duration, Instant},
};
use thiserror::Error;
use vibeguard_core::redact;
use vibeguard_repository::RepositorySource;

#[derive(Debug, Error)]
pub enum GitError {
    #[error("Git is not installed")]
    NotInstalled,
    #[error("Git command timed out")]
    Timeout,
    #[error("Git failed: {0}")]
    Failed(String),
    #[error("I/O: {0}")]
    Io(String),
}
#[derive(Clone, Debug)]
pub struct GitRunner {
    pub timeout: Duration,
}
#[derive(Clone, Debug)]
pub struct DiffFile {
    pub path: String,
    pub status: String,
    pub additions: u64,
    pub deletions: u64,
}
#[derive(Clone, Debug, Default)]
pub struct DiffSummary {
    pub files: Vec<DiffFile>,
    pub raw: String,
    pub available: bool,
}

impl GitRunner {
    pub fn new(timeout_seconds: u64) -> Self {
        Self {
            timeout: Duration::from_secs(timeout_seconds),
        }
    }
    pub fn run(&self, cwd: Option<&Path>, args: &[&str]) -> Result<Output, GitError> {
        let mut command = Command::new("git");
        command
            .args(args)
            .env("GIT_TERMINAL_PROMPT", "0")
            .env("GCM_INTERACTIVE", "never")
            .env("GIT_CONFIG_NOSYSTEM", "0");
        if let Some(path) = cwd {
            command.current_dir(path);
        }
        let child = command.output().map_err(|error| {
            if error.kind() == io::ErrorKind::NotFound {
                GitError::NotInstalled
            } else {
                GitError::Io(error.to_string())
            }
        })?;
        if !child.status.success() {
            return Err(GitError::Failed(redact(&String::from_utf8_lossy(
                &child.stderr,
            ))));
        }
        Ok(child)
    }
    pub fn output(&self, cwd: Option<&Path>, args: &[&str]) -> Result<String, GitError> {
        Ok(String::from_utf8_lossy(&self.run(cwd, args)?.stdout)
            .trim()
            .to_owned())
    }
    pub fn command_with_timeout(
        &self,
        cwd: Option<&Path>,
        program: &str,
        args: &[String],
    ) -> Result<Output, GitError> {
        let mut command = Command::new(program);
        command
            .args(args)
            .env("GIT_TERMINAL_PROMPT", "0")
            .env("GCM_INTERACTIVE", "never")
            .env(
                "GIT_SSH_COMMAND",
                format!(
                    "ssh -o BatchMode=yes -o ConnectTimeout={}",
                    self.timeout.as_secs()
                ),
            );
        if let Some(path) = cwd {
            command.current_dir(path);
        }
        let mut child = command.spawn().map_err(|error| {
            if error.kind() == io::ErrorKind::NotFound {
                GitError::NotInstalled
            } else {
                GitError::Io(error.to_string())
            }
        })?;
        let started = Instant::now();
        loop {
            if let Some(status) = child
                .try_wait()
                .map_err(|error| GitError::Io(error.to_string()))?
            {
                let output = child
                    .wait_with_output()
                    .map_err(|error| GitError::Io(error.to_string()))?;
                if status.success() {
                    return Ok(output);
                }
                return Err(GitError::Failed(redact(&String::from_utf8_lossy(
                    &output.stderr,
                ))));
            }
            if started.elapsed() > self.timeout {
                let _ = child.kill();
                let _ = child.wait();
                return Err(GitError::Timeout);
            }
            thread::sleep(Duration::from_millis(25));
        }
    }
    pub fn is_repository(&self, root: &Path) -> bool {
        self.output(Some(root), &["rev-parse", "--is-inside-work-tree"])
            .is_ok_and(|value| value == "true")
    }
    pub fn head(&self, root: &Path) -> Option<String> {
        self.output(Some(root), &["rev-parse", "HEAD"]).ok()
    }
    pub fn diff(&self, root: &Path) -> DiffSummary {
        if !self.is_repository(root) || self.head(root).is_none() {
            return DiffSummary::default();
        }
        let raw = self
            .output(Some(root), &["diff", "HEAD", "--", "."])
            .unwrap_or_default();
        let stats = self
            .output(Some(root), &["diff", "HEAD", "--numstat", "--", "."])
            .unwrap_or_default();
        let names = self
            .output(Some(root), &["diff", "HEAD", "--name-status", "--", "."])
            .unwrap_or_default();
        let mut counts = std::collections::BTreeMap::new();
        for line in stats.lines() {
            let parts: Vec<_> = line.split('\t').collect();
            if parts.len() == 3 {
                counts.insert(
                    parts[2].to_owned(),
                    (parts[0].parse().unwrap_or(0), parts[1].parse().unwrap_or(0)),
                );
            }
        }
        let mut files = Vec::new();
        for line in names.lines() {
            let parts: Vec<_> = line.split('\t').collect();
            if parts.len() >= 2 {
                let path = parts
                    .last()
                    .map_or_else(String::new, |item| (*item).to_owned());
                let (additions, deletions) = counts.get(&path).copied().unwrap_or((0, 0));
                let status = match parts[0].chars().next() {
                    Some('A') => "added",
                    Some('D') => "deleted",
                    Some('R') => "renamed",
                    _ => "modified",
                }
                .to_owned();
                files.push(DiffFile {
                    path,
                    status,
                    additions,
                    deletions,
                });
            }
        }
        DiffSummary {
            files,
            raw,
            available: true,
        }
    }
    pub fn fetch_bare(
        &self,
        source: &RepositorySource,
        cache: &Path,
        reference: Option<&str>,
        refresh: bool,
    ) -> Result<String, GitError> {
        let url = source
            .safe_remote_url()
            .ok_or_else(|| GitError::Failed("remote source required".to_owned()))?;
        if !cache.exists() {
            let args = vec![
                "clone".to_owned(),
                "--bare".to_owned(),
                "--filter=blob:none".to_owned(),
                "--depth=1".to_owned(),
                "--no-tags".to_owned(),
                url,
                cache.display().to_string(),
            ];
            self.command_with_timeout(None, "git", &args)?;
        } else if refresh || reference.is_some() {
            let refname = reference.unwrap_or("HEAD");
            let args = vec![
                format!("--git-dir={}", cache.display()),
                "fetch".to_owned(),
                "--force".to_owned(),
                "--prune".to_owned(),
                "--depth=1".to_owned(),
                "origin".to_owned(),
                refname.to_owned(),
            ];
            self.command_with_timeout(None, "git", &args)?;
        }
        let target = reference.unwrap_or("HEAD");
        self.output(
            None,
            &[
                "--git-dir",
                &cache.display().to_string(),
                "rev-parse",
                target,
            ],
        )
        .map(|value| value.trim().to_owned())
    }
    pub fn tree(
        &self,
        git_dir: &Path,
        commit: &str,
    ) -> Result<Vec<(String, String, u64)>, GitError> {
        let raw = self.output(
            None,
            &[
                "--git-dir",
                &git_dir.display().to_string(),
                "ls-tree",
                "-r",
                "-l",
                "--full-tree",
                commit,
            ],
        )?;
        Ok(raw
            .lines()
            .filter_map(|line| {
                let (left, path) = line.split_once('\t')?;
                let parts: Vec<_> = left.split_whitespace().collect();
                Some((
                    path.to_owned(),
                    parts.get(2)?.to_string(),
                    parts.get(3)?.parse().ok()?,
                ))
            })
            .collect())
    }
    pub fn read_blob(&self, git_dir: &Path, object: &str) -> Result<Vec<u8>, GitError> {
        let output = self.run(
            None,
            &[
                "--git-dir",
                &git_dir.display().to_string(),
                "cat-file",
                "blob",
                object,
            ],
        )?;
        Ok(output.stdout)
    }
}
