//! Minimal stable plugin surface; internal scanner details are intentionally private.

use vibeguard_core::Finding;
pub const API_VERSION: &str = "1";
pub trait RulePack: Send + Sync {
    fn name(&self) -> &'static str;
    fn api_version(&self) -> &'static str {
        API_VERSION
    }
    fn analyze(&self, path: &str, content: &str) -> Vec<Finding>;
}
