# Target catalog: ten high-value trust seams

Each entry: the seam, why it breaks, prior evidence. When reconning a new
project, grep/read for these first.

1. **Symlink boundaries.** Walkers that don't follow symlink roots; zero files
   selected treated as success. Prior: skill-up ListSkillFiles installed zero
   files from symlinked skill dirs while logging "skill installed".
2. **Timeout/kill artifact paths.** What survives when the process is killed?
   SIGTERM grace only saves processes that have a cleanup handler; a framework
   can gracefully kill an adapter that itself dies instantly, leaving
   downstream with nothing. Prior: skill-up lost session-result on timeout;
   fix was framework-synthesized minimal artifacts.
3. **Loader silent fallback.** Parse failure → default value, zero warning.
   Priors: frontmatter-name parse failure → directory-name fallback (skill-up);
   empty-frontmatter skill silently dropped (kimi-code) or zombie-registered
   (Claude Code).
4. **Detected-but-not-told.** Detection logic exists and is accurate (exit
   code, internal flag) but never becomes a user-visible sentence. Priors:
   dsh logged max-tokens to session yet printed nothing; no tool in a
   four-tool matrix ever said "your answer was truncated" (L2 row empty).
5. **Deterministic faults sharing transient-fault retry.** Same prompt + same
   token limit retried whole-turn: will hit the same wall; recovered only
   because the mock's once semantics were kind. Prior: claude code F4/F5.
6. **Tombstone-free logs.** Failed attempt and successful retry serialize
   identically; post-hoc audit cannot tell failure ever happened. Prior:
   codex transcript, all five faults.
7. **Shared-state healing races.** Startup routines repairing shared dirs;
   creation guarded, read/delete naked; half-healed states that raise no
   error. Prior: dsh ENOENT storm, 23/48 process starts.
8. **Main/sub-process double standards.** The main agent accepts truncation
   silently while the sub-agent path has a hard check (or vice versa). Prior:
   kimi-code main vs final-summary.
9. **Assertions/configs bound to actively-refactored surfaces.** Upstream
   narrows a field's semantics; your test asserted the field, not its
   responsibility. Prior: skill-up generated_files → generated_file_sources.
10. **Empty-set treated as healthy.** Filter matches nothing, zero files
    selected, zero cases run — reported as green. Priors: CI green on zero
    matched cases; symlink zero-install. Any count of zero deserves a hard
    error unless explicitly justified.

## Recon method for a fresh codebase

1. Read the entry path of one real user action end to end (request → parse →
   act → report). Note every point where an error is swallowed, defaulted, or
   logged-and-continued.
2. Grep for: `catch` with empty/`None` bodies, `or <default>` on parse
   results, `// TODO`/`FIXME` near error handling, retry loops without error
   taxonomy, `exit 0` paths that skip verification.
3. Check the loader/installer layer specifically — it runs before any user
   intent exists and therefore has the least scrutiny.
4. Check the kill/timeout path specifically — it runs when things are already
   bad and gets the least test coverage.
5. Pick the seam where a wound is (a) realistic, (b) on a path you can force
   the host to walk, (c) decidable by a witness you can build deterministically.
