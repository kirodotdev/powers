#!/usr/bin/env bash
# The git steps the Shipyard skill takes before a push, as one tested script,
# so the agent never pastes file paths or messages into shell commands.
#
#   bash shipyard-git.sh inventory                        files a commit could include
#   bash shipyard-git.sh remotes                          every remote, credentials hidden
#   bash shipyard-git.sh destination                      where a push to origin goes, credentials hidden
#   bash shipyard-git.sh screen [--new-repo] PATHS_FILE   check those files and the commits a push sends
#   bash shipyard-git.sh commit PATHS_FILE MESSAGE_FILE [CONFIRMED_FILE]
#                                                        commit exactly those paths, with that message
#   bash shipyard-git.sh fetch                            git fetch --prune origin, without prompting
#   bash shipyard-git.sh default-branch                   the push destination's default branch
#   bash shipyard-git.sh push BRANCH [CONFIRMED_FILE]     screen what the push sends, then push that branch
#
# PATHS_FILE holds one path per line, MESSAGE_FILE the commit message, and
# CONFIRMED_FILE the CONTENT_HIT and HISTORY_* lines the user said aren't secrets. The agent
# writes them with its file-writing tool, never through a shell.
#
# Output lines start with an upper-case tag. File contents are never printed;
# commit subjects are, unless they look like a secret, and URLs have their
# credentials hidden. Exit 0: clean or done. 1: hits to show the user.
# 2: stopped, and this step changed nothing (SCREEN_FAILED, PARENT_REPO,
# NOT_A_REPO, NO_ORIGIN, NO_IDENTITY, IN_PROGRESS, NET_FAILED, PUSH_REJECTED,
# PUSH_BLOCKED, HOOK_FAILED, HISTORY_TOO_LONG, INDEX_RESTORE_FAILED), or the
# undo itself failed (UNDO_FAILED): tell the user.
#
# With GIT_SSH set (for example plink), ssh's BatchMode can't be added, so an
# ssh passphrase prompt can still wait for input.
set -u
USER_LC_ALL_SET=${LC_ALL+set}; USER_LC_ALL=${LC_ALL-}
export LC_ALL=C GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never GIT_NO_REPLACE_OBJECTS=1
export GIT_ASKPASS= SSH_ASKPASS=
shopt -s nocasematch

# A secret-looking value, checked case-insensitively by grep -E, git log -G/--grep and [[ =~ ]].
P='PRIVATE KEY|(^|[^A-Za-z])(api[_-]?key|secret|token|pass(w(or)?d)?|pwd|private[_-]?key|credential|auth(orization)?|client-key-data)[A-Za-z0-9_]*[^A-Za-z0-9[:space:]]?[[:space:]]*[:=][[:space:]]*[^A-Za-z0-9[:space:]$]?[A-Za-z0-9_/+=@!#%^&*~-]{8,}([^A-Za-z0-9_/+=@!#%^&*~.(-]|$)|bearer[[:space:]]+[A-Za-z0-9._~+/-]{16,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_-]{20,}|xox[abprs]-|[rs]k_live_|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|eyJ[A-Za-z0-9_-]{10,}\.|hooks\.slack\.com/services/|://[^/[:space:]:@]+:[^/[:space:]@${}]{8,}@'
# Matches P line by line. "stdin": exit 0 on a hit. "files": reads NUL-separated paths and prints
# "hit<TAB>path" and "bin<TAB>path" (any NUL byte) lines; exit 2 if a file can't be read.
MATCH_PL='
  my $re = qr/$ENV{SHIPYARD_P}/i;
  sub hits { my $c = shift; $c =~ tr/\0//d; for my $l (split /\r?\n/, $c) { return 1 if $l =~ $re } return 0 }
  if ($ARGV[0] eq "stdin") { local $/; my $c = <STDIN>; exit(hits(defined $c ? $c : "") ? 0 : 1) }
  $/ = "\0";
  while (my $p = <STDIN>) {
    chomp $p;
    open(my $fh, "<", $p) or do { print STDERR "cannot read $p\n"; exit 2 };
    binmode $fh; my $c = do { local $/; <$fh> }; close $fh; $c = "" unless defined $c;
    print "bin\t$p\n" if index($c, "\0") >= 0;
    print "hit\t$p\n" if hits($c);
  }'
matches() { SHIPYARD_P="$P" perl -e "$MATCH_PL" "$@"; }
# Dependency folders: named once by inventory, never committed.
DEP_NAMES='node_modules|\.venv|venv|__pycache__|\.terraform|\.next'
DEPS="(^|/)($DEP_NAMES)/"
# Names that are never committed, in any case (.env.example, .env.sample and .env.template are fine).
NEVER="(^|/)(\.env(\.[^/]*)?|[^/]*\.env|\.envrc|[^/]*\.(pem|key|p12|pfx|p8|jks|keystore|ppk|kdbx|sqlite|sqlite3|db|dump)|[^/]*\.tfstate([.][^/]*)?|[^/]*\.sql\.gz|id_(rsa|dsa|ecdsa|ed25519)|credentials\.json|[^/]*service[-_]?account[^/]*\.json|\.npmrc|\.pypirc|\.netrc|\.git-credentials|kubeconfig)\$|$DEPS"
ENV_OK='(^|/)\.env\.(example|sample|template)$'
MAX_BYTES=52428800
MAX_MB=$((MAX_BYTES / 1048576))
CAP=200
MAX_HISTORY=${SHIPYARD_MAX_HISTORY:-3000}
MAX_PATCH_BYTES=${SHIPYARD_MAX_PATCH_BYTES:-1073741824}
OUT_DIR=""

TMP=$(mktemp -d 2>/dev/null) || { echo "SCREEN_FAILED cannot make a temp folder"; exit 2; }
cleanup() { [ -n "$TMP" ] && [ -d "$TMP" ] && rm -rf -- "$TMP"; }
trap cleanup EXIT

fail() { echo "SCREEN_FAILED $*"; exit 2; }
never() { [[ $1 =~ $NEVER ]] && ! [[ $1 =~ $ENV_OK ]]; }
bad_name() { [[ $1 == *[[:cntrl:]]* ]]; }
in_repo() { git rev-parse --git-dir >/dev/null 2>&1; }
has_commits() { git rev-parse -q --verify HEAD >/dev/null 2>&1; }
# Run a git command that runs the user's hooks with their own locale and replace refs.
as_user() {
  if [ -n "$USER_LC_ALL_SET" ]; then env -u GIT_NO_REPLACE_OBJECTS LC_ALL="$USER_LC_ALL" "$@"
  else env -u GIT_NO_REPLACE_OBJECTS -u LC_ALL "$@"; fi
}
# A NUL-separated path list as literal pathspecs, so no path is read as a glob.
literal() { perl -0pe 's/^/:(literal)/' < "$1"; }
redact() { sed -E 's#(://)[^/?\#[:space:]]*@#\1***@#g'; }
# One line of git or hook output, hidden if it looks like a secret.
safe_line() { if [[ $1 =~ $P ]]; then echo "[details hidden: they look like a secret]"; else printf '%s\n' "$1" | redact | LC_ALL=C tr -d '\000-\011\013-\037\177' | cut -c1-200; fi; }
err_line() {
  local l
  l=$(grep -E '^(fatal|error|remote|hint|!)' "$TMP/err" 2>/dev/null | head -n 1)
  [ -n "$l" ] || l=$(grep -m1 . "$TMP/err" 2>/dev/null)
  [ -n "$l" ] && safe_line "$l"
}

top_level() {
  in_repo || return 0
  local prefix
  prefix=$(git rev-parse --show-prefix 2>/dev/null) || fail "can't find the repo's top level"
  [ -z "$prefix" ] || { echo "PARENT_REPO $(git rev-parse --show-toplevel)"; exit 2; }
}

# Hosts: parse the real host out of a git URL, ignoring any user:password@.
url_host() {
  local u=$1 rest auth
  case "$u" in
    https://*|ssh://*|git+ssh://*|ssh+git://*) rest=${u#*://}; auth=${rest%%[/?#]*}
           [[ $auth == *[\\[:space:]]* ]] && return 0
           auth=${auth##*@}; auth=${auth%%:*}; printf '%s' "$auth" ;;
    *://*|/*|./*|../*|~*|[A-Za-z]:[\\/]*) ;;
    *:*) rest=${u%%:*}; printf '%s' "${rest##*@}" ;;
  esac
}
# True when a url.<base>.insteadOf or pushInsteadOf rule would rewrite this URL again.
rewritten() {
  local rec v
  while IFS= read -r -d '' rec; do
    v=${rec#*$'\n'}
    [ "$v" != "$rec" ] && [ -n "$v" ] && [[ $1 == "$v"* ]] && return 0
  done < <(git config -z --get-regexp '^url\..*\.(push)?insteadof$' 2>/dev/null)
  return 1
}
is_github() {
  local h real
  rewritten "$1" && return 1
  h=$(url_host "$1")
  [ -n "$h" ] || return 1
  case "$h" in github.com|ssh.github.com|www.github.com) return 0 ;; esac
  # An ssh alias (Host github-work, HostName github.com in ~/.ssh/config).
  if [[ $1 == ssh://* || $1 != *://* ]] && command -v ssh >/dev/null 2>&1; then
    real=$(ssh -G -- "$h" 2>/dev/null | awk '$1 == "hostname" { print $2; exit }')
    case "$real" in github.com|ssh.github.com) return 0 ;; esac
  fi
  return 1
}

# Network git with no prompts or askpass dialogs, keeping the user's own SSH command.
net() {
  if [ -n "${GIT_SSH:-}" ]; then
    git -c core.askPass= "$@"
  else
    local base="${GIT_SSH_COMMAND:-$(git config --get core.sshCommand || echo ssh)}"
    GIT_SSH_COMMAND="$base -o BatchMode=yes" git -c core.askPass= "$@"
  fi
}
net_fail() {
  if grep -q 'Host key verification failed' "$TMP/err"; then
    echo "NET_FAILED host key: this machine hasn't connected to that host before"
  elif grep -qiE 'could not resolve host|network is unreachable|operation not permitted|connection refused|timed out|no route to host' "$TMP/err"; then
    echo "NET_FAILED can't reach the remote: offline, or this client's sandbox blocks the network"
  elif grep -qiE 'src refspec .* does not match' "$TMP/err"; then
    echo "NET_FAILED the branch has no commits to push"
  else
    echo "NET_FAILED the remote needs credentials, or refused access: $(err_line)"
  fi
  exit 2
}
need_origin() {
  in_repo || { echo "NOT_A_REPO"; exit 2; }
  git remote get-url origin >/dev/null 2>&1 || { echo "NO_ORIGIN"; exit 2; }
}
# The one push URL for origin. Returns 1 for more than one URL, 2 if it can't be read, 3 if it starts with '-'.
one_push_url() {
  local u n
  u=$(git remote get-url --push --all origin 2>/dev/null) || return 2
  n=$(printf '%s\n' "$u" | grep -c .)
  [ "$n" -eq 1 ] || return 1
  [[ $u == -* ]] && return 3
  printf '%s\n' "$u"
}

out_dir() {
  [ -n "$OUT_DIR" ] && return 0
  if in_repo; then
    OUT_DIR=$(git rev-parse --git-path shipyard 2>/dev/null) && mkdir -p "$OUT_DIR" 2>/dev/null && [ -w "$OUT_DIR" ] \
      && OUT_DIR=$(cd "$OUT_DIR" && pwd -P) || OUT_DIR=""
  fi
  [ -n "$OUT_DIR" ] || OUT_DIR=$(mktemp -d "${TMPDIR:-/tmp}/shipyard.XXXXXX" 2>/dev/null) || fail "can't save the full list anywhere"
}
# Print up to CAP lines of a file; past CAP, save the whole list and name it on a TAG line.
emit_capped() { # $1 file, $2 tag
  local total
  total=$(wc -l < "$1" | tr -d ' ')
  head -n "$CAP" "$1"
  if [ "$total" -gt "$CAP" ]; then
    out_dir
    cp "$1" "$OUT_DIR/$2.txt" || fail "can't save the full list"
    echo "$2 $total (all of them: $OUT_DIR/$2.txt)"
  fi
}

# Paths from a file (one per line) into a NUL-separated list; sets N.
read_paths() {
  [ -f "${1:-}" ] || fail "no path list file: ${1:-}"
  local p
  N=0
  : > "$TMP/paths"
  while IFS= read -r p || [ -n "$p" ]; do
    p=${p%$'\r'}
    [ -n "$p" ] || continue
    bad_name "$p" && fail "a path in the list has a control character"
    case "/$p/" in
      *//*|*/./*|*/../*) fail "write each path from the repo's top folder, the way git shows it (src/app.py): $p" ;;
    esac
    printf '%s\0' "$p" >> "$TMP/paths"
    N=$((N + 1))
  done < "$1"
}

# Read `git log -z --name-only --format=%x01%h` output; print "hash<TAB>bad<TAB>path" per file.
log_names() {
  local tok c=""
  while IFS= read -r -d '' tok; do
    if [[ $tok == $'\x01'* ]]; then c=${tok#$'\x01'}; continue; fi
    tok=${tok#$'\n'}
    [ -n "$tok" ] || continue
    # A name with a line break or other control character is printed quoted, and flagged.
    if bad_name "$tok"; then printf '%s\t1\t%s\n' "$c" "$(printf '%q' "$tok")"
    else printf '%s\t0\t%s\n' "$c" "$tok"; fi
  done
}

inventory() {
  local -a G
  if in_repo; then
    top_level
    G=(git -c core.quotePath=false)
  else
    echo "NOT_A_REPO"
    git --git-dir="$TMP/scratch.git" --work-tree=. init -q 2>/dev/null || fail "git can't list this folder"
    G=(git -c core.quotePath=false --git-dir="$TMP/scratch.git" --work-tree=.)
  fi
  "${G[@]}" status --porcelain -z --untracked-files=all > "$TMP/status" 2>/dev/null || fail "git status failed"
  find . -path ./.git -prune -o -type f -size +$((MAX_BYTES / 1024))k -print 2>/dev/null | sed 's#^\./##' > "$TMP/big"
  local big=$'\n'"$(cat "$TMP/big")"$'\n'
  : > "$TMP/deps"; : > "$TMP/out"
  local rec xy path from
  while IFS= read -r -d '' rec; do
    xy=${rec:0:2}; path=${rec:3}
    if [[ $xy == R* || $xy == C* ]]; then
      IFS= read -r -d '' from || from=""
      if [[ $xy == R* ]] && [ -n "$from" ]; then
        if bad_name "$from"; then echo "BAD_NAME $(printf '%q' "$from")" >> "$TMP/out"; else echo "DELETED $from" >> "$TMP/out"; fi
      fi
    fi
    if bad_name "$path"; then
      echo "BAD_NAME $(printf '%q' "$path")" >> "$TMP/out"
    elif [[ $path =~ $DEPS ]]; then
      printf '%s\n' "$path" >> "$TMP/deps"
    elif [[ $xy == DD || $xy == AU || $xy == UD || $xy == UA || $xy == DU || $xy == AA || $xy == UU ]]; then
      echo "UNMERGED $path" >> "$TMP/out"
    elif [[ $xy == *D* ]]; then
      echo "DELETED $path" >> "$TMP/out"
    elif never "$path"; then
      echo "NEVER $path" >> "$TMP/out"
    elif [[ $big == *$'\n'"$path"$'\n'* ]]; then
      echo "TOO_BIG $path" >> "$TMP/out"
    else
      echo "FILE $path" >> "$TMP/out"
    fi
  done < "$TMP/status"
  emit_capped "$TMP/out" INVENTORY_TOTAL
  # Each dependency folder once, at its top-most level.
  DEPS_RE="^($DEP_NAMES)\$" awk -F/ 'BEGIN { re = ENVIRON["DEPS_RE"] }
    { p = ""; for (i = 1; i < NF; i++) { p = p $i "/"; if (tolower($i) ~ re) { print p; next } } }' "$TMP/deps" \
    | sort | uniq -c | while read -r count dir; do echo "FOLDER $dir $count files"; done > "$TMP/folders"
  emit_capped "$TMP/folders" FOLDERS_TOTAL
}

remotes() {
  in_repo || { echo "NOT_A_REPO"; exit 2; }
  local n u
  while IFS= read -r n; do
    while IFS= read -r u; do
      if is_github "$u"; then echo "REMOTE $n GITHUB $(printf '%s\n' "$u" | redact)"
      else echo "REMOTE $n OTHER $(printf '%s\n' "$u" | redact)"; fi
    done < <(git remote get-url --push --all "$n" 2>/dev/null)
  done < <(git remote)
}

destination() {
  need_origin
  local u
  while IFS= read -r u; do
    if is_github "$u"; then echo "PUSH_TO $(printf '%s\n' "$u" | redact)"
    elif rewritten "$u"; then echo "NOT_GITHUB $(printf '%s\n' "$u" | redact) (a url.*.insteadOf rule rewrites it again)"
    else echo "NOT_GITHUB $(printf '%s\n' "$u" | redact)"; fi
  done < <(git remote get-url --push --all origin)
}

# The commits a push to origin sends, and what in them looks like a secret.
# $1: "whole" for the whole history; otherwise only what the push URL lacks.
# Writes HISTORY_* hit lines to $TMP/historyhits and prints COMMIT lines.
history_screen() {
  : > "$TMP/exclude"
  local url
  local tip=$2 rc=0
  [ "$1" = whole ] || ! git remote get-url origin >/dev/null 2>&1 || { url=$(one_push_url); rc=$?; }
  [ "$rc" -eq 3 ] && fail "origin's push URL starts with '-'"
  [ "$rc" -eq 2 ] && fail "can't read origin's push URL"
  if [ "$1" = whole ] || ! git remote get-url origin >/dev/null 2>&1; then
    echo "RANGE whole history"
  elif [ "$rc" -ne 0 ]; then
    echo "RANGE whole history (origin pushes to more than one URL)"
  else
    net ls-remote -- "$url" > "$TMP/remote" 2>"$TMP/err" || net_fail
    # Exclude only commits the destination has now, not stale local tracking refs.
    cut -f1 "$TMP/remote" | sort -u | git cat-file --batch-check='%(objectname) %(objecttype)' 2>/dev/null \
      | awk '$2 == "commit" { print "^" $1 }' > "$TMP/exclude"
    echo "RANGE commits the push destination doesn't have"
  fi
  # Pin what user config could change about the output we parse.
  local -a L=(git -c core.quotePath=false -c log.showSignature=false -c color.ui=never -c diff.noprefix=false
    -c diff.mnemonicPrefix=false -c diff.relative=false -c log.diffMerges=separate
    log --root --no-color --no-ext-diff --no-renames --encoding=none --stdin "$tip")
  # Two-parent merges as remerge diffs where git has them; octopus merges (which remerge skips) against each parent.
  local -a DM=(-m) OCTO=(-m)
  git log --diff-merges=remerge -1 "$tip" >/dev/null 2>&1 && DM=(--diff-merges=remerge)
  git log --diff-merges=separate -1 "$tip" >/dev/null 2>&1 && OCTO=(--diff-merges=separate)
  DM+=(--max-parents=2); OCTO+=(--min-parents=3)
  "${L[@]}" --format='%h%x09%s' < "$TMP/exclude" > "$TMP/commits" 2>/dev/null || fail "git log failed"
  local h s total
  total=$(wc -l < "$TMP/commits" | tr -d ' ')
  if [ "$total" -gt "$MAX_HISTORY" ]; then
    echo "HISTORY_TOO_LONG $total commits would need screening, more than $MAX_HISTORY: ask the user to push this history themselves"
    exit 2
  fi
  while IFS=$'\t' read -r h s; do
    if [[ $s == *[[:cntrl:]]* ]]; then echo "COMMIT $h [subject hidden: it has control characters]"
    elif [[ $s =~ $P ]]; then echo "COMMIT $h [subject hidden: it looks like a secret]"
    else echo "COMMIT $h $s"; fi
  done < "$TMP/commits" > "$TMP/commitlines"
  emit_capped "$TMP/commitlines" COMMITS_TOTAL
  [ "$total" -gt "$CAP" ] || echo "COMMITS_TOTAL $total"

  # The same range was screened a moment ago (screen, then push): reuse it.
  local key cache
  # Keyed on the range and on this script, so an updated scanner never reuses an old result.
  key=$( { echo "$tip"; cat "$TMP/exclude"; cat -- "$(git rev-parse --git-path shallow)" "$(git rev-parse --git-path info/grafts)" 2>/dev/null
           echo; cat -- "$0"; } | git hash-object --stdin) || fail "git hash-object failed"
  cache=$(cache_dir)/$key
  # A cache file counts only if it ends with the END line written after the last hit.
  if [ -f "$cache" ] && [ -O "$cache" ] && [ "$(tail -n 1 "$cache")" = END ]; then
    sed '$d' "$cache" > "$TMP/historyhits"; return 0
  fi

  # Commit messages, subject and body.
  set -o pipefail
  "${L[@]}" --format='%x01%h%x02%B' < "$TMP/exclude" 2>/dev/null | SHIPYARD_P="$P" perl -e '
      my $re = qr/$ENV{SHIPYARD_P}/i; local $/ = "\x01";
      while (my $r = <STDIN>) { chomp $r; next unless $r =~ /^(\S+)\x02(.*)$/s; my ($h, $b) = ($1, $2); $b =~ tr/\0//d;
        for my $l (split /\r?\n/, $b) { if ($l =~ $re) { print "HISTORY_MESSAGE_HIT $h\n"; last } } }' > "$TMP/msghits" \
    || fail "couldn't scan the commit messages"
  set +o pipefail
  # Never-commit and unreadable file names in any commit, merges included; each commit is its own hit.
  { "${L[@]}" "${DM[@]}" -z --name-only --format='%x01%h' < "$TMP/exclude" && "${L[@]}" "${OCTO[@]}" -z --name-only --format='%x01%h' < "$TMP/exclude"; } \
    > "$TMP/names" 2>/dev/null || fail "git log failed"
  local c path
  log_names < "$TMP/names" | while IFS=$'\t' read -r c bad path; do
    if [ "$bad" = 1 ] || never "$path"; then printf '%s\t%s\n' "$c" "$path"; fi
  done | awk -F'\t' '!seen[$0]++ { print "HISTORY_NAME_HIT " $1 " " $2 }' > "$TMP/namehits"
  # Secret-looking added or removed lines, in one pass over the patches (text or not, whatever .gitattributes says).
  # Stops (exit 3) past MAX_PATCH_BYTES of patch text, so a huge history ends with a tag, not a timeout.
  { "${L[@]}" "${DM[@]}" --text --no-textconv -p --src-prefix=a/ --dst-prefix=b/ --format='%x01%h' < "$TMP/exclude" \
      && "${L[@]}" "${OCTO[@]}" --text --no-textconv -p --src-prefix=a/ --dst-prefix=b/ --format='%x01%h' < "$TMP/exclude"; } 2>/dev/null \
    | SHIPYARD_P="$P" SHIPYARD_MAX="$MAX_PATCH_BYTES" perl -ne '
        BEGIN { $re = qr/$ENV{SHIPYARD_P}/i; $max = $ENV{SHIPYARD_MAX}; $n = 0; $c = ""; $p = ""; $q = ""; $h = 0; $lfs = 0 }
        # A header path as git wrote it: C-quoted when it has odd characters. Unquote, then drop the a/ or b/.
        sub path { my ($s, $pre) = @_; my $raw = $s;
          if ($s =~ /^"(.*)"$/s) { $s = $1; my %e = (n => "\n", t => "\t", r => "\r", a => "\a", b => "\b", f => "\f", v => "\x0b");
            $s =~ s/\\([0-7]{3}|.)/length($1) == 3 ? chr(oct($1)) : (exists $e{$1} ? $e{$1} : $1)/ge; }
          return "" if $s eq "/dev/null";
          $s =~ s/^\Q$pre\E//;
          # A name with control characters stays as git quoted it, so it cannot fake an output line.
          return $s =~ /[[:cntrl:]]/ ? $raw : $s }
        $n += length; exit 3 if $n > $max;
        chomp;
        if (/^\x01(\S+)$/) { $c = $1; $h = 0; next }
        if (/^diff --git /) { $h = 1; $p = ""; $q = ""; $lfs = 0; next }
        if ($h) {
          if (/^--- (.*?)\t?$/) { $q = path($1, "a/") }
          elsif (/^\+\+\+ (.*?)\t?$/) { my $d = path($1, "b/"); $p = $d eq "" ? $q : $d }
          elsif (/^@@/) { $h = 0 }
          next;
        }
        # A Git LFS pointer, new or changed: the LFS hook uploads the real content, which is never screened here.
        $lfs = 1 if /^[ +-]version (?:https:\/\/git-lfs\.github\.com\/spec\/v1|https:\/\/hawser\.github\.com\/spec\/v1|http:\/\/git-media\.io\/v\/2)\s*$/;
        if ($lfs && /^\+oid sha256:/) { my $k = "L$c\t$p"; print "HISTORY_LFS_HIT $c $p\n" unless $seen{$k}++ }
        next unless /^[+-](.*)$/s;
        my $l = $1;
        # NUL bytes: binary content, or UTF-16 text, which matches once they are dropped.
        if (index($l, "\0") >= 0) { $l =~ tr/\0//d; my $k = "B$c\t$p"; print "HISTORY_BINARY_NOT_SCANNED $c $p\n" unless $seen{$k}++ }
        if ($l =~ $re) { my $k = "$c\t$p"; print "HISTORY_CONTENT_HIT $c $p\n" unless $seen{$k}++ }
      ' > "$TMP/contenthits"
  local st=("${PIPESTATUS[@]}")
  if [ "${st[1]}" = 3 ]; then
    echo "HISTORY_TOO_LONG the commits' changes are more than $MAX_PATCH_BYTES bytes to screen: ask the user to push this history themselves"
    exit 2
  fi
  [ "${st[0]}" = 0 ] && [ "${st[1]}" = 0 ] || fail "couldn't scan the commits' changes"
  cat "$TMP/msghits" "$TMP/namehits" "$TMP/contenthits" > "$TMP/historyhits"
  # Write the whole result and its END line to a temp name, then rename it into place.
  { cat "$TMP/historyhits" && echo END; } > "$cache.$$" 2>/dev/null && mv -f "$cache.$$" "$cache" 2>/dev/null || rm -f "$cache.$$"
}

# A private, per-user folder for screen results, so push can reuse what screen just did.
cache_dir() {
  local d="${TMPDIR:-/tmp}/shipyard-git-cache-$(id -u)"
  if [ ! -d "$d" ]; then mkdir -m 700 "$d" 2>/dev/null || { echo "$TMP"; return; }; fi
  if [ -O "$d" ] && [ ! -L "$d" ]; then echo "$d"; else echo "$TMP"; fi
}
# Each confirmed CONTENT_HIT as "blob<TAB>path"; exact confirmed lines in $TMP/okexact.
read_confirmed() {
  : > "$TMP/okpairs"; : > "$TMP/okexact"
  [ -n "${1:-}" ] || return 0
  [ -f "$1" ] || fail "no confirmed-hits file: $1"
  tr -d '\r' < "$1" > "$TMP/okexact"
  sed -n -E 's/^CONTENT_HIT ([0-9a-f]+) (.*)$/\1	\2/p' "$TMP/okexact" > "$TMP/okpairs"
}
# The blob id git stores for a symlink with this target.
link_blob() { printf '%s' "$1" | git hash-object --stdin; }
# "blob<TAB>path" for the working-tree files in a NUL-separated list (as git would store them).
blob_pairs() { # $1 NUL list
  tr '\0' '\n' < "$1" > "$TMP/bp.paths"
  [ -s "$TMP/bp.paths" ] || return 0
  local -a G=(git)
  if ! in_repo; then
    [ -d "$TMP/scratch.git" ] || git --git-dir="$TMP/scratch.git" --work-tree=. init -q 2>/dev/null || fail "git can't read this folder"
    G=(git --git-dir="$TMP/scratch.git" --work-tree=.)
  fi
  # --stdin-paths reads a path that starts with a double quote as a quoted one, so quote every path.
  perl -pe 's/(["\\])/\\$1/g; s/^/"/; s/$/"/' < "$TMP/bp.paths" \
    | "${G[@]}" hash-object --stdin-paths > "$TMP/bp.blobs" 2>/dev/null || fail "git hash-object failed"
  paste "$TMP/bp.blobs" "$TMP/bp.paths"
}

screen() {
  local mode=dest
  if [ "${1:-}" = "--new-repo" ]; then mode=whole; shift; fi
  top_level
  read_paths "${1:-}"
  : > "$TMP/filehits"; : > "$TMP/scan"
  local p link h
  while IFS= read -r -d '' p; do
    if never "$p"; then
      echo "NAME_HIT $p" >> "$TMP/filehits"
    elif [ -L "$p" ]; then
      # Git stores a symlink as its target text; check that, never what it points to.
      link=$(readlink -- "$p") || fail "couldn't read the link $p"
      [[ $link =~ $P ]] && echo "CONTENT_HIT $(link_blob "$link") $p" >> "$TMP/filehits"
    elif [ ! -e "$p" ]; then
      echo "DELETED $p"
    elif [ -d "$p" ]; then
      fail "$p is a folder: list its files"
    elif [ ! -f "$p" ] || [ ! -r "$p" ]; then
      fail "$p isn't a readable regular file"
    else
      printf '%s\0' "$p" >> "$TMP/scan"
    fi
  done < "$TMP/paths"
  if [ -s "$TMP/scan" ]; then
    perl -0ne 'chomp; print "$_\0" if -s $_ > '"$MAX_BYTES" < "$TMP/scan" > "$TMP/big" || fail "couldn't size the files"
    perl -0ne 'chomp; print "$_\0" if -s $_ <= '"$MAX_BYTES" < "$TMP/scan" > "$TMP/small" || fail "couldn't size the files"
    while IFS= read -r -d '' p; do echo "TOO_BIG $p" >> "$TMP/filehits"; done < "$TMP/big"
    matches files < "$TMP/small" > "$TMP/match" 2>"$TMP/err" || fail "couldn't read every file: $(err_line)"
    sed -n 's/^hit	//p' "$TMP/match" | tr '\n' '\0' > "$TMP/content"
    blob_pairs "$TMP/content" | while IFS=$'\t' read -r h p; do echo "CONTENT_HIT $h $p"; done >> "$TMP/filehits"
    # Content with NUL bytes is matched with them dropped (UTF-16 text), but may still hide a secret: name it.
    sed -n 's/^bin	//p' "$TMP/match" | while IFS= read -r p; do echo "BINARY_NOT_SCANNED $p"; done
  fi
  emit_capped "$TMP/filehits" FILE_HITS_TOTAL
  echo "FILES_CHECKED $N"
  local hits
  hits=$(wc -l < "$TMP/filehits" | tr -d ' ')

  if ! in_repo; then echo "NO_REPO"
  elif ! has_commits; then echo "NO_COMMITS"
  else
    history_screen "$mode" "$(git rev-parse HEAD)"
    emit_capped "$TMP/historyhits" HISTORY_HITS_TOTAL
    hits=$((hits + $(grep -vc '^HISTORY_BINARY_NOT_SCANNED ' "$TMP/historyhits" || true)))
  fi

  if [ "$hits" -gt 0 ]; then echo "SCREEN_HITS $hits"; exit 1; fi
  echo "SCREEN_CLEAN"
}

commit() {
  in_repo || fail "not a git repo yet: run git init first"
  top_level
  [ -f "${2:-}" ] && [ -s "$2" ] || fail "no commit message file, or it's empty"
  matches stdin < "$2" && fail "the commit message looks like it holds a secret: rewrite it"
  git -c user.useConfigOnly=true var GIT_COMMITTER_IDENT >/dev/null 2>&1 || {
    echo "NO_IDENTITY git has no user.name and user.email: ask the user to set them"; exit 2; }
  local gd f what
  gd=$(git rev-parse --git-dir)
  for f in MERGE_HEAD:merge REBASE_HEAD:rebase rebase-merge:rebase rebase-apply:rebase CHERRY_PICK_HEAD:cherry-pick REVERT_HEAD:revert; do
    what=${f#*:}
    [ -e "$gd/${f%%:*}" ] && { echo "IN_PROGRESS a $what is in progress: finish or abort it first"; exit 2; }
  done
  [ -z "$(git ls-files -u)" ] || { echo "IN_PROGRESS there are unmerged files"; exit 2; }
  read_paths "${1:-}"
  [ "$N" -gt 0 ] || fail "no paths given: nothing committed"
  read_confirmed "${3:-}"
  local p link
  : > "$TMP/scan"
  while IFS= read -r -d '' p; do
    never "$p" && fail "$p is a never-commit file"
    if [ -L "$p" ]; then
      link=$(readlink -- "$p") || fail "couldn't read the link $p"
      if [[ $link =~ $P ]] && ! grep -qxF "$(link_blob "$link")	$p" "$TMP/okpairs"; then
        fail "the link $p looks like it holds a secret and the user hasn't confirmed it: run screen again"
      fi
      continue
    fi
    [ -d "$p" ] && fail "$p is a folder: list its files"
    [ -f "$p" ] && printf '%s\0' "$p" >> "$TMP/scan"
  done < "$TMP/paths"
  if [ -s "$TMP/scan" ]; then
    perl -0ne 'chomp; print "$_\n" if -s $_ > '"$MAX_BYTES" < "$TMP/scan" > "$TMP/big" || fail "couldn't size the files"
    [ -s "$TMP/big" ] && fail "a file is over $MAX_MB MB, so it can't go in: $(head -n 1 "$TMP/big" | while IFS= read -r p; do safe_line "$p"; done)"
  fi
  # Re-screen the files as they are now; only hits the user confirmed, with that exact content, may go in.
  if [ -s "$TMP/scan" ]; then
    matches files < "$TMP/scan" > "$TMP/match" 2>"$TMP/err" || fail "couldn't read every file: $(err_line)"
    sed -n 's/^hit	//p' "$TMP/match" | tr '\n' '\0' > "$TMP/nowhits"
    blob_pairs "$TMP/nowhits" | grep -vxF -f "$TMP/okpairs" > "$TMP/unconfirmed" || true
    [ -s "$TMP/unconfirmed" ] && fail "files look like they hold a secret and the user hasn't confirmed them as they are now: run screen again"
  fi
  # What was screened, blob by path: after the commit, only what differs from this is screened again.
  blob_pairs "$TMP/scan" > "$TMP/expected"
  while IFS= read -r -d '' p; do
    [ -L "$p" ] && printf '%s\t%s\n' "$(link_blob "$(readlink -- "$p")")" "$p" >> "$TMP/expected"
  done < "$TMP/paths"
  literal "$TMP/paths" > "$TMP/pathspecs"

  local idx old
  idx=$(git rev-parse --git-path index)
  old=$(git rev-parse -q --verify HEAD || true)
  if [ -f "$idx" ]; then
    cp -p "$idx" "$TMP/index.bak" && cmp -s "$idx" "$TMP/index.bak" || fail "couldn't back up the git index: nothing changed"
  fi
  restore() {
    if [ -f "$TMP/index.bak" ]; then
      if ! { cp -p "$TMP/index.bak" "$idx" && cmp -s "$TMP/index.bak" "$idx"; }; then
        out_dir; cp -p "$TMP/index.bak" "$OUT_DIR/index.bak"
        echo "INDEX_RESTORE_FAILED the git index couldn't be put back; a copy is at $OUT_DIR/index.bak"; exit 2
      fi
    else
      rm -f -- "$idx"
    fi
  }
  undo() {
    local now; now=$(git rev-parse --short HEAD 2>/dev/null)
    if [ -n "$old" ]; then git update-ref HEAD "$old" 2>/dev/null; else git update-ref -d HEAD 2>/dev/null; fi || {
      echo "UNDO_FAILED commit $now should have been undone but is still on the branch: tell the user before anything else"; exit 2; }
    restore
  }

  git add --pathspec-from-file="$TMP/pathspecs" --pathspec-file-nul >"$TMP/out" 2>"$TMP/err" || { restore; fail "git add failed: $(err_line)"; }
  as_user git commit -q -F "$2" --pathspec-from-file="$TMP/pathspecs" --pathspec-file-nul </dev/null >"$TMP/out" 2>"$TMP/err" || {
    restore; fail "git commit failed: $(err_line)"; }

  # Exactly one new commit, on top of where the branch was: a hook's extra commit would hide this one.
  if [ -n "$old" ]; then [ "$(git rev-parse -q --verify HEAD^ 2>/dev/null)" = "$old" ]; else ! git rev-parse -q --verify HEAD^ >/dev/null 2>&1; fi || {
    undo; fail "a git hook made another commit, so the commit was undone"; }
  # Check what actually landed: hooks can add files or change them.
  git diff-tree --no-commit-id --name-only -r -z --root HEAD > "$TMP/landed" 2>/dev/null || { undo; fail "couldn't read the new commit"; }
  tr '\0' '\n' < "$TMP/paths" | sort -u > "$TMP/listed"
  tr '\0' '\n' < "$TMP/landed" | sort -u > "$TMP/landed.txt"
  comm -13 "$TMP/listed" "$TMP/landed.txt" > "$TMP/extra"
  if [ -s "$TMP/extra" ]; then
    undo
    fail "a git hook added files you didn't list, so the commit was undone: $(head -n 5 "$TMP/extra" | while IFS= read -r p; do safe_line "$p"; done | tr '\n' ' ')"
  fi
  # Hooks can change the message too.
  if git -c log.showSignature=false log -1 --encoding=none --format=%B HEAD | matches stdin; then
    undo
    fail "a commit hook put a secret-looking line in the message, so the commit was undone"
  fi
  # Mode, blob and path of each file that landed, for the size and changed-content checks.
  git diff-tree -r -z --root --no-commit-id HEAD 2>/dev/null \
    | perl -0ne 'chomp; if (/^:\d+ (\d+) \S+ (\S+) \S+$/) { ($m, $b) = ($1, $2); next }
                 print "$m\t$b\t$_\n" if defined $m && $m ne "000000"; undef $m' > "$TMP/landedmeta" || { undo; fail "couldn't read the new commit"; }
  cut -f2 "$TMP/landedmeta" | git cat-file --batch-check='%(objectsize)' 2>/dev/null | awk -v max="$MAX_BYTES" '$1 + 0 > max' > "$TMP/landedbig"
  if [ -s "$TMP/landedbig" ]; then undo; fail "a file over $MAX_MB MB landed in the commit (a git hook may have grown it), so the commit was undone"; fi
  # Files or links a hook changed after the screen: screen them as they landed.
  cut -f2,3 "$TMP/landedmeta" | grep -vxF -f "$TMP/expected" > "$TMP/changed" || true
  local blob
  while IFS=$'\t' read -r blob p; do
    if git cat-file blob "$blob" | matches stdin && ! grep -qxF "$blob	$p" "$TMP/okpairs"; then
      undo
      fail "what landed in the commit looks like it holds a secret (a git hook may have changed it), so the commit was undone"
    fi
  done < "$TMP/changed"
  echo "COMMITTED $(git rev-parse --short HEAD) $N paths"
}

push() {
  local b="${1:-}" confirmed="${2:-}" url
  need_origin
  git check-ref-format --branch "$b" >/dev/null 2>&1 || fail "not a branch name: $b"
  [ "$(git branch --show-current)" = "$b" ] || fail "HEAD isn't on $b"
  local rc=0 sha
  url=$(one_push_url) || rc=$?
  [ "$rc" -eq 3 ] && fail "origin's push URL starts with '-'"
  [ "$rc" -eq 2 ] && fail "can't read origin's push URL"
  [ "$rc" -eq 0 ] || fail "origin pushes to more than one URL: ask the user which one, and push to it alone"
  rewritten "$url" && fail "a url.*.insteadOf rule in git config rewrites $(printf '%s\n' "$url" | redact) again: ask the user to push this one themselves"
  is_github "$url" || fail "origin pushes to $(printf '%s\n' "$url" | redact), which isn't GitHub"
  # Screen and push this one commit, even if the branch moves in between.
  sha=$(git rev-parse --verify -q HEAD) || fail "HEAD has no commits"
  read_confirmed "$confirmed"

  # Screen exactly what this push sends; hits the user confirmed aren't secrets don't stop it.
  ( history_screen dest "$sha" ) > "$TMP/range" || { grep -vE '^(COMMIT |COMMITS_TOTAL )' "$TMP/range"; exit 2; }
  grep -v '^HISTORY_BINARY_NOT_SCANNED ' "$TMP/historyhits" | grep -vxF -f "$TMP/okexact" > "$TMP/open0" || true
  # A content hit confirmed before the commit: same file, same content, in the commit that landed it.
  : > "$TMP/open"
  local line c f blob
  while IFS= read -r line; do
    if [[ $line == "HISTORY_CONTENT_HIT "* ]]; then
      c=${line#HISTORY_CONTENT_HIT }; f=${c#* }; c=${c%% *}
      blob=$(printf '%s:%s\n' "$c" "$f" | git cat-file --batch-check='%(objectname)' 2>/dev/null)
      grep -qxF "$blob	$f" "$TMP/okpairs" && continue
    fi
    printf '%s\n' "$line" >> "$TMP/open"
  done < "$TMP/open0"
  if [ -s "$TMP/open" ]; then
    grep -E '^RANGE' "$TMP/range"
    emit_capped "$TMP/open" HISTORY_HITS_TOTAL
    echo "SCREEN_HITS $(wc -l < "$TMP/open" | tr -d ' ') (nothing was pushed)"
    exit 1
  fi

  net push --no-follow-tags --recurse-submodules=no -u -- "$url" "$sha:refs/heads/$b" >"$TMP/out" 2>"$TMP/err" && {
    git branch -q --set-upstream-to="origin/$b" "$b" 2>/dev/null; echo "PUSHED $b"; return; }
  local hooks
  hooks=$(git config --get core.hooksPath || git rev-parse --git-path hooks)
  if grep -qiE 'GH013|push protection|cannot contain secrets' "$TMP/err"; then
    echo "PUSH_BLOCKED GitHub found a secret in these commits and refused the push"; exit 2
  elif grep -q '\[remote rejected\]' "$TMP/err"; then
    echo "PUSH_BLOCKED the remote declined the push: $(err_line)"; exit 2
  elif grep -qE '\[rejected\].*(fetch first|non-fast-forward)' "$TMP/err"; then
    echo "PUSH_REJECTED $b: the remote has commits this branch doesn't"; exit 2
  elif [ -x "$hooks/pre-push" ] && ! grep -qE '^remote: |\[rejected\]' "$TMP/err"; then
    echo "HOOK_FAILED the local pre-push hook stopped the push: $(err_line)"; exit 2
  fi
  net_fail
}

case "${1:-}" in
  inventory) inventory ;;
  remotes) remotes ;;
  destination) destination ;;
  screen) shift; screen "$@" ;;
  commit) shift; commit "$@" ;;
  fetch) need_origin; net fetch --prune --quiet origin >"$TMP/out" 2>"$TMP/err" || net_fail; echo "FETCHED" ;;
  default-branch)
    need_origin
    rc=0; url=$(one_push_url) || rc=$?
    [ "$rc" -eq 3 ] && fail "origin's push URL starts with '-'"
    [ "$rc" -eq 2 ] && fail "can't read origin's push URL"
    [ "$rc" -eq 0 ] || { echo "UNKNOWN origin pushes to more than one URL"; exit 0; }
    out=$(net ls-remote --symref -- "$url" HEAD 2>"$TMP/err") || net_fail
    ref=$(printf '%s\n' "$out" | sed -n 's#^ref: refs/heads/\([^[:space:]]*\)[[:space:]]*HEAD$#\1#p')
    if [ -n "$ref" ]; then echo "DEFAULT $ref"
    elif [ -z "$out" ]; then echo "EMPTY_REMOTE"
    else echo "UNKNOWN"; fi ;;
  push) shift; push "$@" ;;
  *) echo "usage: shipyard-git.sh inventory | remotes | destination | screen [--new-repo] PATHS_FILE | commit PATHS_FILE MESSAGE_FILE [CONFIRMED_FILE] | fetch | default-branch | push BRANCH [CONFIRMED_FILE]" >&2; exit 2 ;;
esac
