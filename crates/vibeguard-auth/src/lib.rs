//! Authentication diagnostics; credentials are delegated to the existing Git environment.

#[derive(Clone, Debug)]
pub struct AuthStatus {
    pub ssh_agent: bool,
    pub github_cli: bool,
    pub ci_token_present: bool,
    pub credential_helper_configured: bool,
}
pub fn status() -> AuthStatus {
    AuthStatus {
        ssh_agent: std::env::var_os("SSH_AUTH_SOCK").is_some(),
        github_cli: executable_exists("gh"),
        ci_token_present: std::env::var_os("VIBEGUARD_GIT_TOKEN").is_some(),
        credential_helper_configured: git_credential_helper(),
    }
}
pub fn login_github_message() -> String {
    if executable_exists("gh") {
        "GitHub CLI detected. Run `gh auth login`; VibeGuard will reuse its Git credentials."
            .to_owned()
    } else {
        "GitHub CLI is not installed. Configure SSH or your Git credential helper, then retry."
            .to_owned()
    }
}
fn executable_exists(name: &str) -> bool {
    std::env::var_os("PATH").is_some_and(|paths| {
        std::env::split_paths(&paths).any(|path| {
            path.join(if cfg!(windows) {
                format!("{name}.exe")
            } else {
                name.to_owned()
            })
            .exists()
        })
    })
}
fn git_credential_helper() -> bool {
    std::process::Command::new("git")
        .args(["config", "--get", "credential.helper"])
        .output()
        .is_ok_and(|output| output.status.success() && !output.stdout.is_empty())
}
