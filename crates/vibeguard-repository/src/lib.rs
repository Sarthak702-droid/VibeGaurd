//! Validated local and remote repository source parsing.

use std::path::PathBuf;
use thiserror::Error;
use url::Url;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RepositorySource {
    LocalPath {
        path: PathBuf,
    },
    Remote {
        url: Url,
        original: String,
    },
    ScpLikeSsh {
        user: Option<String>,
        host: String,
        path: String,
    },
}
#[derive(Debug, Error)]
pub enum RepositorySourceError {
    #[error("unsupported or dangerous repository transport: {0}")]
    Unsupported(String),
    #[error("invalid repository source: {0}")]
    Invalid(String),
}

impl RepositorySource {
    pub fn parse(value: &str) -> Result<Self, RepositorySourceError> {
        if value.starts_with("ext::") || value.contains("::") || value.starts_with("file:") {
            return Err(RepositorySourceError::Unsupported(value.to_owned()));
        }
        if let Some((left, path)) = value.split_once(':').filter(|(left, path)| {
            !left.contains('/') && !path.starts_with("//") && !path.is_empty()
        }) {
            let (user, host) = match left.split_once('@') {
                Some((user, host)) => (Some(user.to_owned()), host.to_owned()),
                None => (None, left.to_owned()),
            };
            if host.is_empty() || path.contains("..") {
                return Err(RepositorySourceError::Invalid(value.to_owned()));
            }
            return Ok(Self::ScpLikeSsh {
                user,
                host,
                path: path.trim_start_matches('/').to_owned(),
            });
        }
        if let Ok(url) = Url::parse(value) {
            if !matches!(url.scheme(), "https" | "ssh" | "git") {
                return Err(RepositorySourceError::Unsupported(url.scheme().to_owned()));
            }
            if url.host_str().is_none() {
                return Err(RepositorySourceError::Invalid(value.to_owned()));
            }
            return Ok(Self::Remote {
                url,
                original: value.to_owned(),
            });
        }
        Ok(Self::LocalPath {
            path: PathBuf::from(value),
        })
    }
    pub fn normalized_identity(&self) -> String {
        match self {
            Self::LocalPath { path } => format!("local:{}", path.display()),
            Self::ScpLikeSsh { user, host, path } => format!(
                "ssh://{}{host}/{path}",
                user.as_ref()
                    .map(|item| format!("{item}@"))
                    .unwrap_or_default()
            ),
            Self::Remote { url, .. } => {
                let mut normalized = url.clone();
                let _ = normalized.set_username("");
                let _ = normalized.set_password(None);
                normalized.to_string().trim_end_matches('/').to_owned()
            }
        }
    }
    pub fn safe_remote_url(&self) -> Option<String> {
        match self {
            Self::Remote { .. } | Self::ScpLikeSsh { .. } => Some(self.normalized_identity()),
            Self::LocalPath { .. } => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::RepositorySource;

    #[test]
    fn removes_url_credentials_from_identity() {
        let source =
            RepositorySource::parse("https://TOKEN@github.com/company/repository.git").unwrap();
        assert_eq!(
            source.normalized_identity(),
            "https://github.com/company/repository.git"
        );
    }

    #[test]
    fn rejects_dangerous_transport() {
        assert!(RepositorySource::parse("ext::sh -c bad").is_err());
    }
}
