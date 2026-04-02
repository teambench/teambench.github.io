#!/usr/bin/env bash
# SECITER-02 Grader
# Runs both test suites (6 security + 4 functional = 10 total)
# Score = passing_tests / 10
# Exit 0 if all 10 pass, exit 1 otherwise.

set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/workspace" && pwd)"
TOTAL_TESTS=10

cd "$WORKSPACE"

if [ ! -d "node_modules" ]; then
  echo "[grader] Installing dependencies..."
  npm install --silent 2>/dev/null || npm install
fi

echo "[grader] Running security tests..."
SEC_OUTPUT=$(./node_modules/.bin/jest --testPathPattern=test/security/headers.test.js \
  --forceExit --detectOpenHandles --no-coverage --json 2>/dev/null || true)

echo "[grader] Running functional tests..."
FUNC_OUTPUT=$(./node_modules/.bin/jest --testPathPattern=test/functional/app.test.js \
  --forceExit --detectOpenHandles --no-coverage --json 2>/dev/null || true)

count_passed() {
  local json="$1"
  echo "$json" | node -e "
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
})" 2>/dev/null || echo "0"
}

SEC_PASSED=$(count_passed "$SEC_OUTPUT")
FUNC_PASSED=$(count_passed "$FUNC_OUTPUT")

TOTAL_PASSED=$(( SEC_PASSED + FUNC_PASSED ))
TOTAL_PASSED=$(( TOTAL_PASSED > TOTAL_TESTS ? TOTAL_TESTS : TOTAL_PASSED ))
TOTAL_PASSED=$(( TOTAL_PASSED < 0 ? 0 : TOTAL_PASSED ))

SCORE=$(node -e "console.log(($TOTAL_PASSED / $TOTAL_TESTS).toFixed(4))")

echo "----------------------------------------"
echo "SECITER-02 Results"
echo "  Security tests : $SEC_PASSED / 6"
echo "  Functional tests: $FUNC_PASSED / 4"
echo "  Total passed   : $TOTAL_PASSED / $TOTAL_TESTS"
echo "  Score          : $SCORE"
echo "----------------------------------------"
echo "score=$SCORE"

if [ "$TOTAL_PASSED" -eq "$TOTAL_TESTS" ]; then
  exit 0
else
  exit 1
fi
