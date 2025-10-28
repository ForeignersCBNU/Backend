#!/usr/bin/env bash
set -euo pipefail
base=${BASE_URL:-http://127.0.0.1:8000}

# login (assumes you already registered that user)
TOKEN=$(curl -s -X POST "$base/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"test1234"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# upload file
FILE_ID=$(curl -s -F "file=@/etc/hosts" -H "Authorization: Bearer $TOKEN" \
  "$base/files/upload" | python -c "import sys,json;print(json.load(sys.stdin)['file_id'])")

# poll summary twice
curl -s "$base/files/$FILE_ID/summary" -H "Authorization: Bearer $TOKEN" | python -m json.tool
sleep 1
curl -s "$base/files/$FILE_ID/summary" -H "Authorization: Bearer $TOKEN" | python -m json.tool

# create test
TEST_JSON=$(curl -s -X POST "$base/tests/create" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"file_id\":\"$FILE_ID\",\"num_questions\":1}")
echo "$TEST_JSON" | python -m json.tool
TEST_ID=$(python - <<'PY' <<<"$TEST_JSON"
import sys,json;print(json.loads(sys.stdin.read())["test_id"])
PY
)

# fetch test & answer B
ANS=$(curl -s "$base/tests/$TEST_ID" -H "Authorization: Bearer $TOKEN" | \
python - <<'PY'
import sys,json
d=json.load(sys.stdin)
print(json.dumps({"answers":[{"question_id":d["items"][0]["question_id"],"answer":"B"}]}))
PY
)

# submit & show result
curl -s -X POST "$base/tests/$TEST_ID/submit" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d "$ANS" | python -m json.tool

# export PDF
curl -s -H "Authorization: Bearer $TOKEN" \
  -o test.pdf "$base/tests/$TEST_ID/export.pdf?with_answers=1"
echo "PDF written to test.pdf"
