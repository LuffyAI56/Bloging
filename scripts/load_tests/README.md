Load test skeletons for the Blog API

k6 (JS)

Run locally (install k6 first):

k6 run scripts/load_tests/k6_load_test.js --env BASE_URL=http://127.0.0.1:8000

Adjust `options` at the top of the script for VUs and duration.

Locust (Python)

Install locust (prefer separate venv):

pip install locust

Run:

locust -f scripts/load_tests/locustfile.py --host=http://127.0.0.1:8000

Open the web UI at http://localhost:8089 and start a test.

Notes

- These are skeletons for quick smoke and load runs. For CI-grade load testing, run in a controlled environment and collect metrics from both the app and DB.
- Ensure you do not run load tests against production without coordination.
