# migrate/

Templates `honey install --slim-instructions` writes over `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`. The originals are backed up, and `honey uninstall` restores them.

They hold the author's personal preferences. **Edit them before you use the flag**, or skip the flag and keep your own files. honey-stack works the same either way: its workflow rules come from the plugin, not from these files.
