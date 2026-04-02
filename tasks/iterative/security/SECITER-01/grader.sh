#!/usr/bin/env bash
# SECITER-01 Grader
# Runs the 8-test Jest suite and outputs score = passing_tests / 8
# Exit 0 if all tests pass, exit 1 otherwise.

set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/workspace" && pwd)"
TOTAL_TESTS=8

cd "$WORKSPACE"

# Install dependencies silently if node_modules missing
if [ ! -d "node_modules" ]; then
  echo "[grader] Installing dependencies..."
  npm install --silent 2>/dev/null || npm install
fi

echo "[grader] Running test suite..."

# Run jest, capture output
TEST_OUTPUT=$(./node_modules/.bin/jest --testPathPattern=test/security/auth.test.js \
  --forceExit \
  --detectOpenHandles \
  --no-coverage \
  --json \
  2>/dev/null || true)

# Parse JSON output for pass/fail counts
PASSED=$(echo "$TEST_OUTPUT" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  const raw = chunks.join('');
  // Jest --json outputs a JSON blob; find it (it may have prefixed log lines)
  const jsonStart = raw.indexOf('{\"');
  if (jsonStart === -1) { console.log(0); process.exit(0); }
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

FAILED=$(echo "$TEST_OUTPUT" | node -e "
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  const raw = chunks.join('');
  const jsonStart = raw.indexOf('{\"');
  if (jsonStart === -1) { console.log($TOTAL_TESTS); process.exit(0); }
  try {
    const data = JSON.parse(raw.slice(jsonStart));
    let failed = 0;
    (data.testResults || []).forEach(suite => {
      (suite.testResults || []).forEach(t => {
        if (t.status === 'failed') failed++;
      });
    });
    console.log(failed);
  } catch(e) { console.log($TOTAL_TESTS); }
})" 2>/dev/null || echo "$TOTAL_TESTS")

# Clamp to valid range
PASSED=$(( PASSED > TOTAL_TESTS ? TOTAL_TESTS : PASSED ))
PASSED=$(( PASSED < 0 ? 0 : PASSED ))

SCORE=$(node -e "console.log(($PASSED / $TOTAL_TESTS).toFixed(4))")

echo "----------------------------------------"
echo "SECITER-01 Results"
echo "  Passed : $PASSED / $TOTAL_TESTS"
echo "  Failed : $FAILED"
echo "  Score  : $SCORE"
echo "----------------------------------------"
echo "score=$SCORE"

if [ "$PASSED" -eq "$TOTAL_TESTS" ]; then
  exit 0
else
  exit 1
fi
