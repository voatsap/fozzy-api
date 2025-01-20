import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  // Define your load test stages
  // 1. Ramp up from 0 to 100 virtual users (VUs) over 30 seconds
  // 2. Hold at 100 VUs for 1 minute
  // 3. Ramp down to 0 VUs over 10 seconds
  stages: [
    { duration: '30s', target: 100 },
    { duration: '1m', target: 100 },
    { duration: '10s', target: 0 },
  ],
};

// Base URL of your API (change to your actual DNS or IP)
const BASE_URL = 'http://fozzy.inbox.wine:8000'; 

export default function () {
  // For example, query the /suggestions endpoint.
  // If your endpoint is GET /suggestions?wine_name=XYZ&n_results=10
  let url = `${BASE_URL}/suggestions?wine_name=Tarlant%20Brut%20Cuvee%20Louis%20Tarlant&n_results=10`;

  // Make the request
  let res = http.get(url);

  // Check for successful response
  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  // Sleep to simulate user wait time between requests
  sleep(1);
}