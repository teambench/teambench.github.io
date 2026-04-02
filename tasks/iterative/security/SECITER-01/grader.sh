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

# Run jest with --json, capture output (stderr has human output, stdout has JSON)
TEST_JSON=$(./node_modules/.bin/jest --testPathPattern=test/security/auth.test.js \
  --forceExit \
  --detectOpenHandles \
  --no-coverage \
  --json \
  2>/dev/null || true)

# Parse using top-level numPassedTests / numFailedTests from Jest JSON
PASSED=$(node -e "
try {
  const raw = $(printf '%s' "$TEST_JSON" | node -e "
    const c=[]; process.stdin.on('data',d=>c.push(d)); process.stdin.on('end',()=>{
      console.log(JSON.stringify(c.join('')));
    });" 2>/dev/null || echo '""');
  const data = JSON.parse(raw);
  console.log(data.numPassedTests || 0);
} catch(e) { console.log(0); }
" 2>/dev/null || echo "0")

# Simpler approach: use node to parse the JSON directly from a temp file
TMPFILE=$(mktemp)
echo "$TEST_JSON" > "$TMPFILE"

PASSED=$(node -e "
const fs = require('fs');
try {
  const raw = fs.readFileSync('$TMPFILE', 'utf8');
  const jsonStart = raw.indexOf('{');
  const data = JSON.parse(raw.slice(jsonStart));
  console.log(data.numPassedTests || 0);
} catch(e) { console.log(0); }
" 2>/dev/null || echo "0")

FAILED=$(node -e "
const fs = require('fs');
try {
  const raw = fs.readFileSync('$TMPFILE', 'utf8');
  const jsonStart = raw.indexOf('{');
  const data = JSON.parse(raw.slice(jsonStart));
  console.log(data.numFailedTests || 0);
} catch(e) { console.log($TOTAL_TESTS); }
" 2>/dev/null || echo "$TOTAL_TESTS")

rm -f "$TMPFILE"

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
