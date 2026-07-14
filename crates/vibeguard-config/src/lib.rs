//! Configuration loading with CLI > environment > project > user > defaults precedence.

use directories::ProjectDirs;
use serde::{Deserialize, Serialize};
use std::{
    env, fs,
    path::{Path, PathBuf},
};
use thiserror::Error;

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct Config {
    pub version: u32,
    pub scan: ScanConfig,
    pub policies: PolicyConfig,
    pub verification: VerificationConfig,
    pub git: GitConfig,
    pub ignore: Vec<String>,
    pub secret_suppressions: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct ScanConfig {
    pub max_file_size: u64,
    pub max_repository_size: u64,
    pub max_files: u64,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct PolicyConfig {
    pub fail_on: String,
    pub blocking_score: u8,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct VerificationConfig {
    pub timeout_seconds: u64,
    pub custom_commands: Vec<Vec<String>>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct GitConfig {
    pub timeout_seconds: u64,
    pub retries: u8,
    pub cache_enabled: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            version: 1,
            scan: ScanConfig::default(),
            policies: PolicyConfig::default(),
            verification: VerificationConfig::default(),
            git: GitConfig::default(),
            ignore: Vec::new(),
            secret_suppressions: vec!["FAKE_TEST_TOKEN_DO_NOT_USE".to_owned()],
        }
    }
}
impl Default for ScanConfig {
    fn default() -> Self {
        Self {
            max_file_size: 1_048_576,
            max_repository_size: 2_147_483_648,
            max_files: 250_000,
        }
    }
}
impl Default for PolicyConfig {
    fn default() -> Self {
        Self {
            fail_on: "critical".to_owned(),
            blocking_score: 80,
        }
    }
}
impl Default for VerificationConfig {
    fn default() -> Self {
        Self {
            timeout_seconds: 300,
            custom_commands: Vec::new(),
        }
    }
}
impl Default for GitConfig {
    fn default() -> Self {
        Self {
            timeout_seconds: 30,
            retries: 2,
            cache_enabled: true,
        }
    }
}

#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("could not read configuration {path}: {message}")]
    Read { path: String, message: String },
    #[error("invalid configuration {path}: {message}")]
    Parse { path: String, message: String },
}

pub fn project_path(root: &Path) -> PathBuf {
    root.join(".vibeguard.toml")
}
pub fn user_path() -> Option<PathBuf> {
    ProjectDirs::from("dev", "VibeGuard", "VibeGuard")
        .map(|dirs| dirs.config_dir().join("config.toml"))
}
pub fn load(root: &Path) -> Result<Config, ConfigError> {
    let mut config = Config::default();
    if let Some(path) = user_path().filter(|path| path.exists()) {
        merge(&mut config, read(&path)?);
    }
    let path = project_path(root);
    if path.exists() {
        merge(&mut config, read(&path)?);
    }
    if let Ok(value) = env::var("VIBEGUARD_MAX_FILE_SIZE") {
        config.scan.max_file_size = value.parse().map_err(|_| ConfigError::Parse {
            path: "VIBEGUARD_MAX_FILE_SIZE".to_owned(),
            message: "must be an integer".to_owned(),
        })?;
    }
    if let Ok(value) = env::var("VIBEGUARD_FAIL_ON") {
        config.policies.fail_on = value;
    }
    Ok(config)
}
pub fn write_default(root: &Path) -> Result<PathBuf, ConfigError> {
    let path = project_path(root);
    if !path.exists() {
        let content =
            toml::to_string_pretty(&Config::default()).map_err(|error| ConfigError::Parse {
                path: path.display().to_string(),
                message: error.to_string(),
            })?;
        fs::write(&path, content).map_err(|error| ConfigError::Read {
            path: path.display().to_string(),
            message: error.to_string(),
        })?;
    }
    Ok(path)
}
fn read(path: &Path) -> Result<Config, ConfigError> {
    let content = fs::read_to_string(path).map_err(|error| ConfigError::Read {
        path: path.display().to_string(),
        message: error.to_string(),
    })?;
    toml::from_str(&content).map_err(|error| ConfigError::Parse {
        path: path.display().to_string(),
        message: error.to_string(),
    })
}
fn merge(base: &mut Config, update: Config) {
    if update.version != 1 {
        base.version = update.version;
    }
    base.scan = update.scan;
    base.policies = update.policies;
    base.verification = update.verification;
    base.git = update.git;
    if !update.ignore.is_empty() {
        base.ignore = update.ignore;
    }
    if !update.secret_suppressions.is_empty() {
        base.secret_suppressions = update.secret_suppressions;
    }
}
