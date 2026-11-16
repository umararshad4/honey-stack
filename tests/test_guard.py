from helpers import REPO  # noqa: F401
from honey.guard import check
from honey import modes

assert check("git --no-pager push -f origin main")[1] == "ask"
assert check("rm -rf ~")[1] == "deny"
assert check('bash -lc "rm -rf /"')[1] == "deny"
assert check('echo "rm -rf /"') == (None, None)
assert check("git checkout -- src/app.py") == (None, None)
assert check("git checkout -- .")[1] == "ask"
assert check("ls -la") == (None, None)
assert check(None) == (None, None)
assert check("echo a > /tmp/x > /tmp/y > /tmp/z") == (None, None)   # redirect scan terminates
assert check("cat x > /dev/disk0")[1] == "deny"
assert check("git push origin +main")[1] == "ask"
assert check("git checkout .")[1] == "ask"
assert check("git branch --delete --force feat")[1] == "ask" and check("git branch -d -f feat")[1] == "ask"
assert check("git branch -d feat") == (None, None)
assert check("kubectl -n prod delete pod x")[1] == "ask"
assert check("terraform -chdir=infra destroy")[1] == "ask"
assert check("kubectl get pods") == (None, None)
assert modes.parse_command("/honey explain") == ["explain"]
assert modes.parse_command("honey off") == ["off"]
assert modes.parse_command("stop honey.") == ["off"]
assert modes.parse_command("add a normal mode toggle") is None
assert modes.parse_command("/honey how do I debug this") is None
assert modes.parse_command("honey default direct") == ["default", "direct"]
# absolute rm -rf: cleanup inside the workspace or a temp dir passes; roots, home and escapes still warn (#55, #58)
import os, tempfile
ws = "/Users/dev/code/app"
assert check("rm -rf /Users/dev/code/app/node_modules /Users/dev/code/app/dist", cwd=ws) == (None, None)
assert check("rm -rf /tmp/build-cache", cwd=ws) == (None, None)
assert check("rm -rf /private/tmp/x/y") == (None, None)
assert check(f"rm -rf {os.path.join(tempfile.gettempdir(), 'scratch')}") == (None, None)
assert check(f"rm -rf {ws}", cwd=ws)[1] == "deny"                      # the workspace itself
assert check(f"rm -rf {ws}/*", cwd=ws)[1] == "deny"                    # everything in it
assert check(f"rm -rf {ws}/../other", cwd=ws)[1] == "deny"             # escape via ..
assert check("rm -rf /Users/dev/code/app2", cwd=ws)[1] == "deny"       # sibling prefix
assert check("rm -rf /tmp", cwd=ws)[1] == "deny" and check("rm -rf /tmp/*")[1] == "deny"
assert check("rm -rf /tmp/../etc")[1] == "deny"
assert check("rm -rf /Users/dev/Documents", cwd="/Users/dev")[1] == "deny"  # cwd = home is no exemption
assert check("rm -rf /etc/x", cwd="/")[1] == "deny"
assert check("rm -rf /Users/dev/code/app/build")[1] == "deny"          # no cwd known
assert check("rm -rf /tmp/x | xargs rm -rf", cwd=ws)[1] == "deny"
# find -delete: same scoped-cleanup rule as rm; only the start paths count
assert check(f"find {ws}/dist -name '*.map' -delete", cwd=ws) == (None, None)
assert check("find /tmp/cache -type f -delete") == (None, None)
assert check("find . -name '*.pyc' -delete") == (None, None)
assert check(f"find {ws} -delete", cwd=ws)[1] == "deny"
assert check("find / -name core -delete", cwd=ws)[1] == "deny"
assert check("find ~ -name x -delete")[1] == "deny"
# heredoc bodies are data unless fed to a shell
assert check("python3 - <<'EOF'\nprint('rm -rf /')\nx = \"unbalanced\nEOF") == (None, None)
assert check("cat > notes.md <<EOF\nrun rm -rf / to wipe it\nEOF") == (None, None)
assert check("bash <<'EOF'\nrm -rf /\nEOF")[1] == "deny"
assert check("cat <<'EOF' | sh\nrm -rf ~\nEOF")[1] == "deny"
assert check("python3 - <<'EOF'\nprint(1)\nEOF\nrm -rf ~")[1] == "deny"     # command after the heredoc
# unparseable command (shlex fails): fallback applies the same scoped rule
assert check('rm -rf /tmp/x; echo "unterminated', cwd=ws) == (None, None)
assert check(f'rm -rf {ws}/build && echo "oops', cwd=ws) == (None, None)
assert check('rm -rf /etc/x; echo "unterminated', cwd=ws)[1] == "deny"
assert check('rm -rf ~; echo "x')[1] == "deny"
assert check('rm -rf /; echo "x')[1] == "deny"
# fail closed: quoted <<, missing terminator, eval/$( ) consumers, find global options
assert check("echo '<<EOF'\nrm -rf /\nEOF")[1] == "deny"
assert check("echo \"x <<EOF\"\nrm -rf ~")[1] == "deny"
assert check("cat <<EOF\nrm -rf /")[1] == "deny"                         # no terminator
assert check('eval "$(cat <<EOF\nrm -rf /\nEOF\n)"')[1] == "deny"
assert check("source /dev/stdin <<EOF\nrm -rf ~\nEOF")[1] == "deny"
assert check("find -L / -name x -delete")[1] == "deny"
assert check("find -O3 -D exec ~ -delete")[1] == "deny"
assert check("find -H /tmp/cache -delete") == (None, None)
print("guard+modes ok")
