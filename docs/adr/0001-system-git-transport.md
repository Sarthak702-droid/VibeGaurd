# ADR 0001: Use system Git for repository transport

Status: accepted

VibeGuard uses the installed Git executable for remote transport and object
access. Rust owns URL validation, process policy, cache lifecycle, scanning,
reports, and all user-facing behavior. Git is invoked with terminal prompts
disabled and SSH batch mode enabled. This preserves user SSH agents, credential
helpers, host configuration, and enterprise Git support without executing code
from scanned repositories. A `GitTransport` interface keeps a native transport
implementation possible later.
