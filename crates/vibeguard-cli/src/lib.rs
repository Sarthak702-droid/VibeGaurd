//! Shared `vibeguard` / `vbg` command implementation.

use clap::{Args, Parser, Subcommand};
use std::{
    fs,
    path::{Path, PathBuf},
    time::Duration,
};
use vibeguard_cache as cache;
use vibeguard_config as config;
use vibeguard_context as context;
use vibeguard_core::{Finding, ScanResult, Severity, VibeGuardError};
use vibeguard_git::GitRunner;
use vibeguard_repository::RepositorySource;

#[derive(Parser)]
#[command(
    name = "vibeguard",
    version,
    about = "Local-first guardrails for AI-assisted software development"
)]
struct Cli {
    #[arg(long, global = true)]
    verbose: bool,
    #[command(subcommand)]
    command: Commands,
}
#[derive(Subcommand)]
enum Commands {
    Init(ProjectArgs),
    Scan(ScanArgs),
    Context(GoalArgs),
    Plan(GoalArgs),
    Prompt(PromptArgs),
    Pack(GoalArgs),
    Verify(VerifyArgs),
    Doctor(ProjectArgs),
    #[command(alias = "diff-explain")]
    Explain(ProjectArgs),
    #[command(alias = "risks")]
    Risk(JsonProjectArgs),
    Secrets(JsonProjectArgs),
    Deps(JsonProjectArgs),
    Report(ReportArgs),
    #[command(alias = "next-prompt")]
    Next(ProjectArgs),
    All(GoalArgs),
    Config {
        #[command(subcommand)]
        command: ConfigCommands,
    },
    Cache {
        #[command(subcommand)]
        command: CacheCommands,
    },
    Auth {
        #[command(subcommand)]
        command: AuthCommands,
    },
    Ci {
        #[command(subcommand)]
        command: CiCommands,
    },
    Precommit {
        #[command(subcommand)]
        command: PrecommitCommands,
    },
    Agents {
        #[command(subcommand)]
        command: AgentCommands,
    },
    Run(RunArgs),
}
#[derive(Args, Clone)]
struct ProjectArgs {
    #[arg(long, short = 'p', default_value = ".")]
    project: PathBuf,
}
#[derive(Args)]
struct JsonProjectArgs {
    #[command(flatten)]
    project: ProjectArgs,
    #[arg(long)]
    json: bool,
}
#[derive(Args)]
struct GoalArgs {
    goal_arg: Option<String>,
    #[arg(long, short = 'g')]
    goal: Option<String>,
    #[arg(long, short = 'p', default_value = ".")]
    project: PathBuf,
    #[arg(long, short = 't', default_value_t = 8000)]
    max_tokens: usize,
    #[arg(long)]
    output: Option<PathBuf>,
}
#[derive(Args)]
struct PromptArgs {
    #[command(flatten)]
    goal: GoalArgs,
    #[arg(long, default_value = "generic")]
    agent: String,
}
#[derive(Args)]
struct ScanArgs {
    source: Option<String>,
    #[arg(long, short = 'p')]
    project: Option<PathBuf>,
    #[arg(long)]
    reference: Option<String>,
    #[arg(long)]
    history: bool,
    #[arg(long)]
    all_branches: bool,
    #[arg(long)]
    include_submodules: bool,
    #[arg(long)]
    include_lfs: bool,
    #[arg(long)]
    no_cache: bool,
    #[arg(long)]
    refresh: bool,
    #[arg(long, default_value = "terminal")]
    format: String,
    #[arg(long)]
    output: Option<PathBuf>,
    #[arg(long)]
    fail_on: Option<String>,
    #[arg(long)]
    non_interactive: bool,
    #[arg(long)]
    timeout: Option<u64>,
    #[arg(long)]
    max_file_size: Option<u64>,
    #[arg(long)]
    max_repository_size: Option<u64>,
    #[arg(long)]
    exclude: Vec<String>,
    #[arg(long)]
    include: Vec<String>,
}
#[derive(Args)]
struct VerifyArgs {
    #[command(flatten)]
    project: ProjectArgs,
    #[arg(long)]
    quick: bool,
    #[arg(long)]
    full: bool,
    #[arg(long)]
    json: bool,
}
#[derive(Args)]
struct ReportArgs {
    #[command(flatten)]
    project: ProjectArgs,
    #[arg(long, short = 'f', default_value = "markdown")]
    format: String,
    #[arg(long)]
    output: Option<PathBuf>,
}
#[derive(Args)]
struct RunArgs {
    agent: String,
    #[arg(long, short = 't')]
    task: String,
    #[arg(long, short = 'p', default_value = ".")]
    project: PathBuf,
}
#[derive(Subcommand)]
enum ConfigCommands {
    Show {
        #[arg(long, short = 'p', default_value = ".")]
        project: PathBuf,
        #[arg(long)]
        json: bool,
    },
    Validate {
        #[arg(long, short = 'p', default_value = ".")]
        project: PathBuf,
    },
    Init {
        #[arg(long, short = 'p', default_value = ".")]
        project: PathBuf,
    },
}
#[derive(Subcommand)]
enum CacheCommands {
    Status,
    Clear,
    Prune,
}
#[derive(Subcommand)]
enum AuthCommands {
    Login { provider: String },
    Status,
    Doctor,
}
#[derive(Subcommand)]
enum CiCommands {
    Generate {
        provider: String,
        #[arg(long, short = 'p', default_value = ".")]
        project: PathBuf,
    },
    Check {
        #[arg(long, short = 'p', default_value = ".")]
        project: PathBuf,
    },
}
#[derive(Subcommand)]
enum PrecommitCommands {
    Install {
        #[arg(long, short = 'p', default_value = ".")]
        project: PathBuf,
    },
}
#[derive(Subcommand)]
enum AgentCommands {
    List,
}

pub fn run() -> i32 {
    match run_inner() {
        Ok(()) => 0,
        Err(error) => {
            eprintln!("✗ {error}");
            error.exit_code()
        }
    }
}
fn run_inner() -> Result<(), VibeGuardError> {
    match Cli::parse().command {
        Commands::Init(args) => init(&args.project),
        Commands::Scan(args) => scan(args),
        Commands::Context(args) => goal_workflow(args, "context"),
        Commands::Plan(args) => goal_workflow(args, "plan"),
        Commands::Prompt(args) => prompt(args),
        Commands::Pack(args) => goal_workflow(args, "pack"),
        Commands::Verify(args) => verify(&args.project.project, args.quick, args.json),
        Commands::Doctor(args) => doctor(&args.project),
        Commands::Explain(args) => explain(&args.project),
        Commands::Risk(args) => findings_command(&args.project.project, args.json, "risk"),
        Commands::Secrets(args) => findings_command(&args.project.project, args.json, "secrets"),
        Commands::Deps(args) => findings_command(&args.project.project, args.json, "deps"),
        Commands::Report(args) => {
            report(&args.project.project, &args.format, args.output.as_deref())
        }
        Commands::Next(args) => next(&args.project),
        Commands::All(args) => all(args),
        Commands::Config { command } => configuration(command),
        Commands::Cache { command } => cache_command(command),
        Commands::Auth { command } => auth(command),
        Commands::Ci { command } => ci(command),
        Commands::Precommit { command } => precommit(command),
        Commands::Agents { command } => agents(command),
        Commands::Run(args) => run_agent(args),
    }
}

fn root(path: &Path) -> Result<PathBuf, VibeGuardError> {
    path.canonicalize()
        .map_err(|error| VibeGuardError::Io(error.to_string()))
}
fn init(project: &Path) -> Result<(), VibeGuardError> {
    let root = root(project)?;
    fs::create_dir_all(root.join(".vibeguard/reports"))
        .map_err(|error| VibeGuardError::Io(error.to_string()))?;
    let config = config::write_default(&root)
        .map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
    println!(
        "VibeGuard initialized successfully.\nCreated {}",
        config.display()
    );
    Ok(())
}
fn local_scan(root: &Path) -> Result<ScanResult, VibeGuardError> {
    let config =
        config::load(root).map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
    let mut scan = vibeguard_scanner::scan(root, &config)?;
    scan.commit = GitRunner::new(config.git.timeout_seconds).head(root);
    Ok(scan)
}
fn scan(args: ScanArgs) -> Result<(), VibeGuardError> {
    let source = args
        .source
        .clone()
        .or_else(|| args.project.as_ref().map(|path| path.display().to_string()))
        .unwrap_or_else(|| ".".to_owned());
    let parsed = RepositorySource::parse(&source)
        .map_err(|error| VibeGuardError::InvalidInput(error.to_string()))?;
    if (args.history || args.all_branches) && args.non_interactive {
        return Err(VibeGuardError::InvalidInput(
            "history/all-branches scans require an explicit interactive confirmation policy"
                .to_owned(),
        ));
    }
    let report = match parsed {
        RepositorySource::LocalPath { path } => local_scan(&path)?,
        remote => remote_scan(&remote, &args)?,
    };
    emit_scan(&report, &args.format, args.output.as_deref())?;
    if let Some(threshold) = args.fail_on.as_deref().and_then(Severity::parse) {
        let findings = analyze_all(&report.root, &report)?;
        if findings.iter().any(|finding| finding.severity >= threshold) {
            return Err(VibeGuardError::InvalidInput(
                "findings exceeded --fail-on threshold".to_owned(),
            ));
        }
    }
    Ok(())
}
fn remote_scan(source: &RepositorySource, args: &ScanArgs) -> Result<ScanResult, VibeGuardError> {
    let identity = source.normalized_identity();
    let entry =
        cache::lock_repository(&identity).map_err(|error| VibeGuardError::Io(error.to_string()))?;
    let git = GitRunner::new(args.timeout.unwrap_or(30));
    let commit = git
        .fetch_bare(
            source,
            &entry.repository_dir(),
            args.reference.as_deref(),
            args.refresh,
        )
        .map_err(|error| VibeGuardError::Git(error.to_string()))?;
    let tree = git
        .tree(&entry.repository_dir(), &commit)
        .map_err(|error| VibeGuardError::Git(error.to_string()))?;
    let mut files = Vec::new();
    let mut stats = vibeguard_core::FileStatistics::default();
    for (path, _object, size) in tree {
        stats.tracked += 1;
        if size > args.max_file_size.unwrap_or(1_048_576) {
            stats.skipped_oversized += 1;
            continue;
        }
        if path
            .split('/')
            .any(|part| [".git", "node_modules", "vendor", "dist", "build"].contains(&part))
        {
            stats.skipped_generated += 1;
            continue;
        }
        if path.ends_with(".pem") || path.ends_with(".key") || path.contains(".env") {
            stats.skipped_sensitive += 1;
            continue;
        }
        files.push(path);
        stats.scanned += 1;
    }
    let detection = vibeguard_scanner::detect(&PathBuf::from("."), &files);
    let important_files = files
        .iter()
        .filter(|path| {
            [
                "package.json",
                "Cargo.toml",
                "pyproject.toml",
                "go.mod",
                "README.md",
            ]
            .contains(&path.as_str())
        })
        .cloned()
        .collect();
    Ok(ScanResult { root: entry.repository_dir(), repository: identity, commit: Some(commit), detection, files, important_files, statistics: stats, warnings: vec!["Remote scan reads committed Git objects only; repository code and hooks were not executed.".to_owned()] })
}
fn emit_scan(scan: &ScanResult, format: &str, output: Option<&Path>) -> Result<(), VibeGuardError> {
    let format = vibeguard_report::Format::parse(format)?;
    let content = match format {
        vibeguard_report::Format::Terminal => format!(
            "✓ Repository detected: {}\n✓ Commit: {}\n✓ {} tracked files discovered\n✓ {} relevant files scanned\nProject type: {}\nLanguages: {}\nFrameworks: {}\nSkipped binaries: {}\nSkipped oversized: {}\nSkipped generated/vendor: {}\n",
            scan.repository,
            scan.commit.as_deref().unwrap_or("working tree"),
            scan.statistics.tracked,
            scan.statistics.scanned,
            scan.detection.primary_type,
            scan.detection.languages.join(", "),
            scan.detection.frameworks.join(", "),
            scan.statistics.skipped_binary,
            scan.statistics.skipped_oversized,
            scan.statistics.skipped_generated
        ),
        vibeguard_report::Format::Json => vibeguard_report::json(scan, &[], &[])?,
        vibeguard_report::Format::Markdown => vibeguard_report::markdown(scan, &[], &[]),
        vibeguard_report::Format::Sarif => vibeguard_report::sarif(&[])?,
    };
    if matches!(format, vibeguard_report::Format::Terminal) && output.is_none() {
        print!("{content}");
    } else {
        let path = vibeguard_report::write(&scan.root, format, &content, output)?;
        println!("Report written: {}", path.display());
    }
    Ok(())
}

fn resolve_goal(args: &GoalArgs) -> Result<&str, VibeGuardError> {
    args.goal
        .as_deref()
        .or(args.goal_arg.as_deref())
        .filter(|goal| !goal.trim().is_empty())
        .ok_or_else(|| {
            VibeGuardError::InvalidInput(
                "missing goal; pass a positional goal or --goal".to_owned(),
            )
        })
}
fn write_artifact(
    root: &Path,
    name: &str,
    output: Option<&Path>,
    content: &str,
) -> Result<PathBuf, VibeGuardError> {
    let path = output
        .map(PathBuf::from)
        .unwrap_or_else(|| root.join(".vibeguard").join(name));
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| VibeGuardError::Io(error.to_string()))?;
    }
    fs::write(&path, content).map_err(|error| VibeGuardError::Io(error.to_string()))?;
    Ok(path)
}
fn goal_workflow(args: GoalArgs, operation: &str) -> Result<(), VibeGuardError> {
    let root = root(&args.project)?;
    let goal = resolve_goal(&args)?.to_owned();
    let scan = local_scan(&root)?;
    let pack = context::build(&root, &scan, &goal, args.max_tokens)?;
    let content = match operation {
        "context" => pack.markdown,
        "plan" => vibeguard_planner::build(&scan, &goal),
        "pack" => format!(
            "# VibeGuard Token-Saving Pack\n\n## Goal\n{goal}\n\n## Estimated Tokens\n{} / {}\n\n## Included Files\n{}\n\n## Excluded Files\n{}\n",
            pack.estimated_tokens,
            args.max_tokens,
            pack.included
                .iter()
                .map(|item| format!("- {} — {}", item.path, item.reason))
                .collect::<Vec<_>>()
                .join("\n"),
            pack.excluded
                .iter()
                .map(|item| format!("- {item}"))
                .collect::<Vec<_>>()
                .join("\n")
        ),
        _ => return Err(VibeGuardError::Internal("unknown workflow".to_owned())),
    };
    let filename = match operation {
        "context" => "context.md",
        "plan" => "task.md",
        _ => "pack.md",
    };
    let path = write_artifact(&root, filename, args.output.as_deref(), &content)?;
    println!(
        "{} written: {}",
        operation.to_ascii_uppercase(),
        path.display()
    );
    Ok(())
}
fn prompt(args: PromptArgs) -> Result<(), VibeGuardError> {
    let root = root(&args.goal.project)?;
    let goal = resolve_goal(&args.goal)?.to_owned();
    let scan = local_scan(&root)?;
    let pack = context::build(&root, &scan, &goal, args.goal.max_tokens)?;
    let files = pack
        .included
        .iter()
        .map(|item| item.path.clone())
        .collect::<Vec<_>>();
    let content = vibeguard_prompt::build(&scan, &goal, &files, &args.agent);
    let path = write_artifact(&root, "prompt.md", args.goal.output.as_deref(), &content)?;
    println!("Prompt written: {}", path.display());
    Ok(())
}
fn verify(project: &Path, quick: bool, json: bool) -> Result<(), VibeGuardError> {
    let root = root(project)?;
    let cfg =
        config::load(&root).map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
    let scan = local_scan(&root)?;
    let checks = vibeguard_verifier::verify(
        &root,
        &scan.detection,
        quick,
        Duration::from_secs(cfg.verification.timeout_seconds),
    );
    let failed = checks.iter().any(|check| {
        !matches!(
            check.status,
            vibeguard_core::CheckStatus::Passed | vibeguard_core::CheckStatus::Skipped
        )
    });
    let content = if json {
        serde_json::to_string_pretty(&checks)
            .map_err(|error| VibeGuardError::Internal(error.to_string()))?
    } else {
        vibeguard_report::markdown(&scan, &[], &checks)
    };
    let path = write_artifact(&root, "reports/verification_report.md", None, &content)?;
    println!("Verification report written: {}", path.display());
    if failed {
        return Err(VibeGuardError::InvalidInput(
            "one or more verification commands failed".to_owned(),
        ));
    }
    Ok(())
}
fn analyze_all(root: &Path, scan: &ScanResult) -> Result<Vec<Finding>, VibeGuardError> {
    let cfg =
        config::load(root).map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
    let git = GitRunner::new(cfg.git.timeout_seconds);
    let diff = git.diff(root);
    let mut findings = vibeguard_secrets::scan(root, &scan.files, &cfg.secret_suppressions);
    findings.extend(vibeguard_deps::analyze(root));
    findings.extend(vibeguard_risk::analyze(&diff));
    Ok(findings)
}
fn findings_command(project: &Path, json: bool, kind: &str) -> Result<(), VibeGuardError> {
    let root = root(project)?;
    let scan = local_scan(&root)?;
    let cfg =
        config::load(&root).map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
    let git = GitRunner::new(cfg.git.timeout_seconds);
    let findings = match kind {
        "risk" => vibeguard_risk::analyze(&git.diff(&root)),
        "secrets" => vibeguard_secrets::scan(&root, &scan.files, &cfg.secret_suppressions),
        "deps" => vibeguard_deps::analyze(&root),
        _ => return Err(VibeGuardError::Internal("unknown analysis".to_owned())),
    };
    if json {
        println!(
            "{}",
            serde_json::to_string_pretty(&findings)
                .map_err(|error| VibeGuardError::Internal(error.to_string()))?
        );
    } else if findings.is_empty() {
        println!("PASS No {} findings detected.", kind);
    } else {
        for finding in &findings {
            println!(
                "{:?} {} {}{}",
                finding.severity,
                finding.rule_id,
                finding.title,
                if finding.file.is_empty() {
                    String::new()
                } else {
                    format!(" ({})", finding.file)
                }
            );
        }
    }
    if kind != "deps"
        && findings
            .iter()
            .any(|finding| finding.severity >= Severity::High)
    {
        return Err(VibeGuardError::InvalidInput(
            "blocking findings detected".to_owned(),
        ));
    }
    Ok(())
}
fn explain(project: &Path) -> Result<(), VibeGuardError> {
    let root = root(project)?;
    let cfg =
        config::load(&root).map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
    let diff = GitRunner::new(cfg.git.timeout_seconds).diff(&root);
    if !diff.available {
        return Err(VibeGuardError::Unsupported(
            "Git diff is unavailable; initialize a repository with a commit".to_owned(),
        ));
    }
    let lines = diff
        .files
        .iter()
        .map(|file| {
            format!(
                "- {}: `{}` (+{}/-{})",
                file.status, file.path, file.additions, file.deletions
            )
        })
        .collect::<Vec<_>>()
        .join("\n");
    let content = format!(
        "# VibeGuard Change Explanation\n\n## What changed\n{}\n\n## Suggested validation\n- Run `vibeguard verify`.\n- Review auth, dependency, configuration, and migration changes.\n",
        if lines.is_empty() {
            "- No changes"
        } else {
            &lines
        }
    );
    let path = write_artifact(&root, "reports/explanation.md", None, &content)?;
    println!("Explanation written: {}", path.display());
    Ok(())
}
fn report(project: &Path, format: &str, output: Option<&Path>) -> Result<(), VibeGuardError> {
    let root = root(project)?;
    let scan = local_scan(&root)?;
    let findings = analyze_all(&root, &scan)?;
    let format = vibeguard_report::Format::parse(format)?;
    let content = match format {
        vibeguard_report::Format::Terminal | vibeguard_report::Format::Markdown => {
            vibeguard_report::markdown(&scan, &findings, &[])
        }
        vibeguard_report::Format::Json => vibeguard_report::json(&scan, &findings, &[])?,
        vibeguard_report::Format::Sarif => vibeguard_report::sarif(&findings)?,
    };
    let path = vibeguard_report::write(&root, format, &content, output)?;
    println!("Report written: {}", path.display());
    if findings
        .iter()
        .any(|finding| finding.severity == Severity::Critical)
    {
        return Err(VibeGuardError::InvalidInput(
            "critical findings detected".to_owned(),
        ));
    }
    Ok(())
}
fn next(project: &Path) -> Result<(), VibeGuardError> {
    let root = root(project)?;
    let scan = local_scan(&root)?;
    let findings = analyze_all(&root, &scan)?;
    let content = format!(
        "# Suggested Next Prompt\n\nCorrect only these findings:\n{}\n\nAdd regression tests and run `vibeguard verify`.\n",
        findings
            .iter()
            .map(|finding| format!("- {:?} {}", finding.severity, finding.title))
            .collect::<Vec<_>>()
            .join("\n")
    );
    let path = write_artifact(&root, "reports/next-prompt.md", None, &content)?;
    println!("Next prompt written: {}", path.display());
    Ok(())
}
fn all(args: GoalArgs) -> Result<(), VibeGuardError> {
    let root = root(&args.project)?;
    init(&root)?;
    let goal = resolve_goal(&args)?.to_owned();
    let scan = local_scan(&root)?;
    let pack = context::build(&root, &scan, &goal, args.max_tokens)?;
    let context_path = write_artifact(&root, "context.md", None, &pack.markdown)?;
    let plan_path = write_artifact(
        &root,
        "task.md",
        None,
        &vibeguard_planner::build(&scan, &goal),
    )?;
    let files = pack
        .included
        .iter()
        .map(|item| item.path.clone())
        .collect::<Vec<_>>();
    let prompt_path = write_artifact(
        &root,
        "prompt.md",
        None,
        &vibeguard_prompt::build(&scan, &goal, &files, "generic"),
    )?;
    println!(
        "Workflow complete:\n- {}\n- {}\n- {}",
        context_path.display(),
        plan_path.display(),
        prompt_path.display()
    );
    Ok(())
}
fn doctor(project: &Path) -> Result<(), VibeGuardError> {
    let root = root(project)?;
    let cfg =
        config::load(&root).map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
    let scan = local_scan(&root)?;
    let git = GitRunner::new(cfg.git.timeout_seconds);
    println!(
        "VibeGuard Doctor\n\nSystem:\n- OS: {}\n- Rust CLI: available\n- Git repository: {}\n- Python runtime: not required\n\nRepository:\n- Path: {}\n- Type: {}\n- Files scanned: {}\n\nSecurity:\n- Scan executes no repository code: yes\n- Git hooks executed during scan: no\n- Submodules fetched by default: no\n- LFS objects downloaded by default: no\n- Credential redaction: enabled\n\nTools:\n- Git: {}\n- SSH agent: {}\n- GitHub CLI: {}",
        std::env::consts::OS,
        if git.is_repository(&root) {
            "detected"
        } else {
            "not detected"
        },
        root.display(),
        scan.detection.primary_type,
        scan.statistics.scanned,
        if GitRunner::new(2).run(None, &["--version"]).is_ok() {
            "available"
        } else {
            "missing"
        },
        if vibeguard_auth::status().ssh_agent {
            "available"
        } else {
            "not detected"
        },
        if vibeguard_auth::status().github_cli {
            "available"
        } else {
            "not detected"
        }
    );
    Ok(())
}
fn configuration(command: ConfigCommands) -> Result<(), VibeGuardError> {
    match command {
        ConfigCommands::Show { project, json } => {
            let root = root(&project)?;
            let cfg = config::load(&root)
                .map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
            if json {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&cfg)
                        .map_err(|error| VibeGuardError::Internal(error.to_string()))?
                );
            } else {
                println!(
                    "{}",
                    toml::to_string_pretty(&cfg)
                        .map_err(|error| VibeGuardError::Internal(error.to_string()))?
                );
            }
            Ok(())
        }
        ConfigCommands::Validate { project } => {
            let root = root(&project)?;
            config::load(&root)
                .map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
            println!("PASS {}", config::project_path(&root).display());
            Ok(())
        }
        ConfigCommands::Init { project } => {
            let root = root(&project)?;
            let path = config::write_default(&root)
                .map_err(|error| VibeGuardError::Configuration(error.to_string()))?;
            println!("Created {}", path.display());
            Ok(())
        }
    }
}
fn cache_command(command: CacheCommands) -> Result<(), VibeGuardError> {
    match command {
        CacheCommands::Status => {
            let (repos, bytes) =
                cache::status().map_err(|error| VibeGuardError::Io(error.to_string()))?;
            println!("Cached repositories: {repos}\nCache size: {bytes} bytes");
        }
        CacheCommands::Clear | CacheCommands::Prune => {
            cache::clear().map_err(|error| VibeGuardError::Io(error.to_string()))?;
            println!("VibeGuard repository cache cleared.");
        }
    }
    Ok(())
}
fn auth(command: AuthCommands) -> Result<(), VibeGuardError> {
    match command {
        AuthCommands::Login { provider } => {
            if provider != "github" {
                return Err(VibeGuardError::InvalidInput(
                    "only 'github' login guidance is currently supported".to_owned(),
                ));
            }
            println!("{}", vibeguard_auth::login_github_message());
        }
        AuthCommands::Status | AuthCommands::Doctor => {
            let status = vibeguard_auth::status();
            println!(
                "Authentication diagnostics\n- SSH agent: {}\n- Git credential helper: {}\n- GitHub CLI: {}\n- CI token: {}\n\nCredentials are never printed or embedded in URLs.",
                status.ssh_agent,
                status.credential_helper_configured,
                status.github_cli,
                status.ci_token_present
            );
        }
    }
    Ok(())
}
fn ci(command: CiCommands) -> Result<(), VibeGuardError> {
    match command {
        CiCommands::Generate { provider, project } => {
            let root = root(&project)?;
            let (path, body) = match provider.as_str() {
                "github" => (
                    root.join(".github/workflows/vibeguard.yml"),
                    "name: VibeGuard\non: [push, pull_request]\npermissions:\n  contents: read\n  security-events: write\njobs:\n  verify:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: dtolnay/rust-toolchain@stable\n      - run: cargo install vibeguard-cli --locked\n      - run: vibeguard ci check\n",
                ),
                "gitlab" => (
                    root.join(".gitlab-ci.yml"),
                    "vibeguard:\n  image: rust:1.85\n  script:\n    - cargo install vibeguard-cli --locked\n    - vibeguard ci check\n",
                ),
                _ => {
                    return Err(VibeGuardError::InvalidInput(
                        "provider must be github or gitlab".to_owned(),
                    ));
                }
            };
            if path.exists() {
                return Err(VibeGuardError::InvalidInput(format!(
                    "refusing to overwrite {}",
                    path.display()
                )));
            }
            if let Some(parent) = path.parent() {
                fs::create_dir_all(parent)
                    .map_err(|error| VibeGuardError::Io(error.to_string()))?;
            }
            fs::write(&path, body).map_err(|error| VibeGuardError::Io(error.to_string()))?;
            println!("Generated {}", path.display());
        }
        CiCommands::Check { project } => {
            let root = root(&project)?;
            report(&root, "markdown", None)?;
            report(&root, "json", None)?;
            report(&root, "sarif", None)?;
        }
    }
    Ok(())
}
fn precommit(command: PrecommitCommands) -> Result<(), VibeGuardError> {
    match command {
        PrecommitCommands::Install { project } => {
            let root = root(&project)?;
            let hook = root.join(".git/hooks/pre-commit");
            if !hook.parent().is_some_and(Path::exists) {
                return Err(VibeGuardError::Unsupported(
                    "not a Git repository".to_owned(),
                ));
            }
            if hook.exists() {
                return Err(VibeGuardError::InvalidInput(format!(
                    "refusing to overwrite {}",
                    hook.display()
                )));
            }
            fs::write(
                &hook,
                "#!/bin/sh\nexec vibeguard verify --quick --project .\n",
            )
            .map_err(|error| VibeGuardError::Io(error.to_string()))?;
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                fs::set_permissions(&hook, fs::Permissions::from_mode(0o755))
                    .map_err(|error| VibeGuardError::Io(error.to_string()))?;
            }
            println!("Installed {}", hook.display());
        }
    }
    Ok(())
}
fn agents(command: AgentCommands) -> Result<(), VibeGuardError> {
    match command {
        AgentCommands::List => println!("Supported agent adapters:\n- codex\n- claude"),
    }
    Ok(())
}
fn run_agent(args: RunArgs) -> Result<(), VibeGuardError> {
    let root = root(&args.project)?;
    let adapter = vibeguard_runner::adapter(&args.agent)?;
    let exit = vibeguard_runner::run(&root, adapter.as_ref(), &args.task)?;
    println!("Agent exited with code {exit}");
    if exit != 0 {
        return Err(VibeGuardError::InvalidInput(
            "agent command failed".to_owned(),
        ));
    }
    Ok(())
}
