//! Dependency manifest checks; vulnerability claims require a separately configured source.

use serde_json::Value;
use std::{fs, path::Path};
use vibeguard_core::{Finding, Severity};
pub fn analyze(root: &Path) -> Vec<Finding> {
    let mut findings = Vec::new();
    let package = root.join("package.json");
    if let Ok(content) = fs::read_to_string(&package) {
        if let Ok(value) = serde_json::from_str::<Value>(&content) {
            for section in ["dependencies", "devDependencies"] {
                if let Some(deps) = value.get(section).and_then(Value::as_object) {
                    for (name, version) in deps {
                        let version = version.as_str().unwrap_or_default();
                        if name.contains("colourama")
                            || name.contains("reqeusts")
                            || name.contains("lodahs")
                        {
                            findings.push(finding(
                                "VG-DEPS-001",
                                "Suspicious dependency spelling",
                                Severity::High,
                                name,
                            ));
                        }
                        if version == "*"
                            || version.starts_with("git+")
                            || version.starts_with("file:")
                        {
                            findings.push(finding(
                                "VG-DEPS-002",
                                "Unpinned or non-registry dependency",
                                Severity::Medium,
                                name,
                            ));
                        }
                    }
                }
            }
        }
    }
    for manifest in [
        "requirements.txt",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
    ] {
        if root.join(manifest).exists() {
            findings.push(Finding { rule_id: "VG-DEPS-INFO".to_owned(), title: "Dependency manifest detected".to_owned(), description: "Vulnerability data was not queried because no vulnerability source is configured.".to_owned(), severity: Severity::Info, category: "dependencies".to_owned(), file: manifest.to_owned(), line: None, evidence: "manifest present".to_owned(), recommended_action: "Review manifest and lockfile changes.".to_owned(), confidence: "high".to_owned(), suppressible: false });
        }
    }
    findings
}
fn finding(rule: &str, title: &str, severity: Severity, package: &str) -> Finding {
    Finding {
        rule_id: rule.to_owned(),
        title: title.to_owned(),
        description: format!("{title}: {package}"),
        severity,
        category: "dependencies".to_owned(),
        file: "package.json".to_owned(),
        line: None,
        evidence: package.to_owned(),
        recommended_action: "Verify publisher, source, version, and license.".to_owned(),
        confidence: "medium".to_owned(),
        suppressible: true,
    }
}
