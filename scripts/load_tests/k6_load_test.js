import http from 'k6/http';
import { sleep, check } from 'k6';

export let options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
  },
};

const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export default function () {
  // Home feed
  let res = http.get(`${BASE}/blog/?limit=10`);
  check(res, {
    'feed status 200': (r) => r.status === 200,
  });

  // Trending tags
  res = http.get(`${BASE}/blog/trending/tags`);
  check(res, { 'trending status 200': (r) => r.status === 200 });

  // Search
  res = http.get(`${BASE}/blog/?search=ai&limit=5`);
  check(res, { 'search status 200': (r) => r.status === 200 });

  sleep(Math.random() * 2);
}
