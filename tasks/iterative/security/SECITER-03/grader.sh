#!/usr/bin/env bash
# SECITER-03 Grader
# Score = 0.5 * (audit_clean ? 1 : 0) + 0.5 * (passing_tests / 12)
# Exit 0 if score == 1.0, exit 1 otherwise.

set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/workspace" && pwd)"
TOTAL_TESTS=12

cd "$WORKSPACE"

if [ ! -d "node_modules" ]; then
  echo "[grader] Installing dependencies..."
  npm install --silent 2>/dev/null || npm install
fi

# ── Step 1: npm audit ──────────────────────────────────────────────────────────
echo "[grader] Running npm audit --production..."
AUDIT_OUTPUT=$(npm audit --production --json 2>/dev/null || true)

CRITICAL=$(echo "$AUDIT_OUTPUT" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(chunks.join(''));
    const meta = data.metadata || {};
    const vulns = meta.vulnerabilities || {};
    console.log((vulns.critical || 0) + (vulns.high || 0));
  } catch(e) { console.log(999); }
})" 2>/dev/null || echo "999")

AUDIT_CLEAN=0
if [ "$CRITICAL" -eq 0 ]; then
  AUDIT_CLEAN=1
  echo "[grader] Audit: CLEAN (0 critical/high)"
else
  echo "[grader] Audit: FAILED ($CRITICAL critical/high vulnerabilities)"
fi

# ── Step 2: Run tests ─────────────────────────────────────────────────────────
echo "[grader] Running integration tests..."

TEST_OUTPUT=$(./node_modules/.bin/jest --testPathPattern=test/integration \
  --forceExit --detectOpenHandles --no-coverage --json 2>/dev/null || true)

PASSED=$(echo "$TEST_OUTPUT" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  const raw = chunks.join('');
  const jsonStart = raw.indexOf('{\"');
  if (jsonStart === -1) { console.log(0); return; }
  try {
    const data = JSON.parse(raw.slice(jsonStart));
    let passed = 0;
    (data.testResults || []).forEach(suite => {
      (suite.testResults || []).forEach(t => {
        if (t.status === 'passed') passed++;
      });
    });
    console.log(passed);
  } catch(e) { console.log(0); }
})" 2>/dev/null || echo "0")

PASSED=$(( PASSED > TOTAL_TESTS ? TOTAL_TESTS : PASSED ))
PASSED=$(( PASSED < 0 ? 0 : PASSED ))

# ── Step 3: Compute weighted score ────────────────────────────────────────────
SCORE=$(node -e "
const auditScore = $AUDIT_CLEAN * 0.5;
const testScore = ($PASSED / $TOTAL_TESTS) * 0.5;
const total = auditScore + testScore;
console.log(total.toFixed(4));
")

echo "----------------------------------------"
echo "SECITER-03 Results"
echo "  Audit clean    : $([ $AUDIT_CLEAN -eq 1 ] && echo 'YES' || echo 'NO')"
echo "  Tests passed   : $PASSED / $TOTAL_TESTS"
echo "  Score          : $SCORE"
echo "    (audit: 0.5 weight, tests: 0.5 weight)"
echo "----------------------------------------"
echo "score=$SCORE"

if [ "$AUDIT_CLEAN" -eq 1 ] && [ "$PASSED" -eq "$TOTAL_TESTS" ]; then
  exit 0
else
  exit 1
fi
