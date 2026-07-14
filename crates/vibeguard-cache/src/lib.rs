//! Secure per-user cache keyed only by credential-free repository identity.

use directories::ProjectDirs;
use fs2::FileExt;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    fs::{self, File},
    path::{Path, PathBuf},
};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum CacheError {
    #[error("cache directory unavailable")]
    Unavailable,
    #[error("cache I/O: {0}")]
    Io(String),
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct CacheMetadata {
    pub schema_version: u8,
    pub repository: String,
    pub last_commit: Option<String>,
    pub default_branch: Option<String>,
    pub is_shallow: bool,
}
pub struct CacheEntry {
    pub root: PathBuf,
    lock: File,
}
impl CacheEntry {
    pub fn repository_dir(&self) -> PathBuf {
        self.root.join("repository.git")
    }
    pub fn scan_cache(&self) -> PathBuf {
        self.root.join("scan-cache")
    }
}
impl Drop for CacheEntry {
    fn drop(&mut self) {
        let _ = FileExt::unlock(&self.lock);
    }
}
pub fn cache_root() -> Result<PathBuf, CacheError> {
    let base = ProjectDirs::from("dev", "VibeGuard", "VibeGuard")
        .ok_or(CacheError::Unavailable)?
        .cache_dir()
        .join("repositories");
    fs::create_dir_all(&base).map_err(|error| CacheError::Io(error.to_string()))?;
    Ok(base)
}
pub fn lock_repository(identity: &str) -> Result<CacheEntry, CacheError> {
    let digest = Sha256::digest(identity.as_bytes());
    let key = format!("{digest:x}");
    let root = cache_root()?.join(key);
    fs::create_dir_all(root.join("scan-cache"))
        .map_err(|error| CacheError::Io(error.to_string()))?;
    let lock = File::create(root.join("repository.lock"))
        .map_err(|error| CacheError::Io(error.to_string()))?;
    lock.lock_exclusive()
        .map_err(|error| CacheError::Io(error.to_string()))?;
    Ok(CacheEntry { root, lock })
}
pub fn clear() -> Result<(), CacheError> {
    let root = cache_root()?;
    for entry in fs::read_dir(&root).map_err(|error| CacheError::Io(error.to_string()))? {
        let path = entry
            .map_err(|error| CacheError::Io(error.to_string()))?
            .path();
        if path.is_dir() {
            fs::remove_dir_all(path).map_err(|error| CacheError::Io(error.to_string()))?;
        }
    }
    Ok(())
}
pub fn status() -> Result<(usize, u64), CacheError> {
    let root = cache_root()?;
    let mut count = 0;
    let mut size = 0;
    walk(&root, &mut count, &mut size)?;
    Ok((count, size))
}
fn walk(path: &Path, count: &mut usize, size: &mut u64) -> Result<(), CacheError> {
    for entry in fs::read_dir(path).map_err(|error| CacheError::Io(error.to_string()))? {
        let path = entry
            .map_err(|error| CacheError::Io(error.to_string()))?
            .path();
        if path.is_dir() {
            if path
                .file_name()
                .is_some_and(|name| name == "repository.git")
            {
                *count += 1;
            }
            walk(&path, count, size)?;
        } else {
            *size += fs::metadata(path)
                .map_err(|error| CacheError::Io(error.to_string()))?
                .len();
        }
    }
    Ok(())
}
