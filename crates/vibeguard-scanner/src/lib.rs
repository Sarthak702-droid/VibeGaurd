//! Bounded local snapshot scanner. It reads files but never executes repository content.

use ignore::WalkBuilder;
use std::{collections::BTreeSet, fs, path::Path};
use vibeguard_config::Config;
use vibeguard_core::{Detection, FileStatistics, ScanResult, VibeGuardError};

const GENERATED: &[&str] = &[
    "node_modules",
    ".git",
    ".vibeguard",
    "target",
    "dist",
    "build",
    ".next",
    "vendor",
    "coverage",
    "__pycache__",
];
const SENSITIVE: &[&str] = &[
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "service-account.json",
];

pub fn scan(root: &Path, config: &Config) -> Result<ScanResult, VibeGuardError> {
    let root = root
        .canonicalize()
        .map_err(|error| VibeGuardError::Io(error.to_string()))?;
    let mut files = Vec::new();
    let mut warnings = Vec::new();
    let mut stats = FileStatistics::default();
    let mut builder = WalkBuilder::new(&root);
    builder
        .hidden(false)
        .git_ignore(true)
        .git_global(true)
        .follow_links(false);
    for entry in builder.build() {
        let entry = match entry {
            Ok(entry) => entry,
            Err(error) => {
                warnings.push(format!("unreadable path: {error}"));
                stats.unreadable += 1;
                continue;
            }
        };
        if entry.file_type().is_none_or(|type_| !type_.is_file()) {
            continue;
        }
        stats.tracked += 1;
        let path = entry.path();
        let relative = match path.strip_prefix(&root) {
            Ok(value) => value.to_string_lossy().replace('\\', "/"),
            Err(_) => continue,
        };
        if relative.split('/').any(|part| GENERATED.contains(&part))
            || config.ignore.iter().any(|ignore| relative.contains(ignore))
        {
            stats.skipped_generated += 1;
            continue;
        }
        if SENSITIVE
            .iter()
            .any(|name| path.file_name().is_some_and(|value| value == *name))
            || relative.ends_with(".pem")
            || relative.ends_with(".key")
        {
            stats.skipped_sensitive += 1;
            continue;
        }
        let metadata = match fs::metadata(path) {
            Ok(value) => value,
            Err(_) => {
                stats.unreadable += 1;
                continue;
            }
        };
        if metadata.len() > config.scan.max_file_size {
            stats.skipped_oversized += 1;
            continue;
        }
        let sample = fs::read(path).unwrap_or_default();
        if sample.iter().take(8192).any(|byte| *byte == 0) {
            stats.skipped_binary += 1;
            continue;
        }
        files.push(relative);
        stats.scanned += 1;
        if stats.scanned >= config.scan.max_files {
            warnings.push(format!(
                "scan limit of {} files reached",
                config.scan.max_files
            ));
            break;
        }
    }
    files.sort();
    let detection = detect(&root, &files);
    let important_files = important(&files);
    Ok(ScanResult {
        root: root.clone(),
        repository: format!("local:{}", root.display()),
        commit: None,
        detection,
        files,
        important_files,
        statistics: stats,
        warnings,
    })
}

pub fn detect(root: &Path, files: &[String]) -> Detection {
    let present = |name: &str| root.join(name).exists();
    let package = fs::read_to_string(root.join("package.json"))
        .unwrap_or_default()
        .to_ascii_lowercase();
    let pyproject = fs::read_to_string(root.join("pyproject.toml"))
        .unwrap_or_default()
        .to_ascii_lowercase();
    let mut languages = BTreeSet::new();
    let mut frameworks = BTreeSet::new();
    let mut manifests = Vec::new();
    let mut tests = Vec::new();
    let mut lints = Vec::new();
    let mut types = Vec::new();
    let mut manager = None;
    if present("package.json") {
        languages.insert("Node.js".to_owned());
        manifests.push("package.json".to_owned());
        manager = Some(
            if present("pnpm-lock.yaml") {
                "pnpm"
            } else if present("yarn.lock") {
                "yarn"
            } else if present("bun.lock") || present("bun.lockb") {
                "bun"
            } else {
                "npm"
            }
            .to_owned(),
        );
        if package.contains("react") {
            frameworks.insert("React".to_owned());
        }
        if package.contains("next") {
            frameworks.insert("Next.js".to_owned());
        }
        if package.contains("expo") {
            frameworks.insert("Expo".to_owned());
        }
    }
    if present("pyproject.toml")
        || present("requirements.txt")
        || files.iter().any(|file| file.ends_with(".py"))
    {
        languages.insert("Python".to_owned());
        manifests.extend(
            [
                "pyproject.toml",
                "requirements.txt",
                "poetry.lock",
                "uv.lock",
            ]
            .into_iter()
            .filter(|name| present(name))
            .map(str::to_owned),
        );
        manager.get_or_insert_with(|| {
            if present("uv.lock") {
                "uv".to_owned()
            } else {
                "pip".to_owned()
            }
        });
        if pyproject.contains("ruff") {
            lints.push("ruff check .".to_owned());
        }
        if pyproject.contains("mypy") {
            types.push("mypy .".to_owned());
        }
    }
    if present("Cargo.toml") {
        languages.insert("Rust".to_owned());
        manifests.push("Cargo.toml".to_owned());
        manager.get_or_insert_with(|| "cargo".to_owned());
        tests.push("cargo test".to_owned());
        lints.push("cargo clippy -- -D warnings".to_owned());
    }
    if present("go.mod") {
        languages.insert("Go".to_owned());
        manifests.push("go.mod".to_owned());
        manager.get_or_insert_with(|| "go modules".to_owned());
        tests.push("go test ./...".to_owned());
    }
    if present("pom.xml") || present("build.gradle") || present("build.gradle.kts") {
        languages.insert("Java".to_owned());
    }
    if present("tsconfig.json") || package.contains("typescript") {
        frameworks.insert("TypeScript".to_owned());
        types.push("tsc".to_owned());
    }
    if present("tests") || pyproject.contains("pytest") {
        tests.push("pytest".to_owned());
    }
    let primary = if frameworks.contains("Next.js") {
        "Next.js".to_owned()
    } else if languages.len() > 1 {
        format!(
            "Mixed: {}",
            languages.iter().cloned().collect::<Vec<_>>().join(", ")
        )
    } else {
        languages
            .iter()
            .next()
            .cloned()
            .unwrap_or_else(|| "Unknown".to_owned())
    };
    Detection {
        primary_type: primary,
        languages: languages.into_iter().collect(),
        frameworks: frameworks.into_iter().collect(),
        package_manager: manager,
        manifests,
        entry_points: [
            "src/main.rs",
            "main.py",
            "app.py",
            "src/index.ts",
            "src/index.js",
            "cmd/main.go",
        ]
        .into_iter()
        .filter(|path| present(path))
        .map(str::to_owned)
        .collect(),
        source_dirs: ["src", "app", "lib", "cmd", "internal"]
            .into_iter()
            .filter(|path| root.join(path).is_dir())
            .map(str::to_owned)
            .collect(),
        test_dirs: ["tests", "test", "spec", "__tests__"]
            .into_iter()
            .filter(|path| root.join(path).is_dir())
            .map(str::to_owned)
            .collect(),
        test_tools: tests,
        lint_tools: lints,
        type_tools: types,
    }
}
fn important(files: &[String]) -> Vec<String> {
    files
        .iter()
        .filter(|file| {
            matches!(
                file.as_str(),
                "package.json"
                    | "pyproject.toml"
                    | "Cargo.toml"
                    | "go.mod"
                    | "README.md"
                    | "Dockerfile"
                    | "tsconfig.json"
                    | ".gitlab-ci.yml"
            ) || file.ends_with("/Dockerfile")
        })
        .cloned()
        .collect()
}
