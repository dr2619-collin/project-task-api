// k6 provides an HTTP client for sending requests to a running API.
import http from "k6/http";
// `check` records pass/fail conditions in the k6 results summary.
import { check } from "k6";

// k6 reads this configuration before it starts virtual users.
export const options = {
  scenarios: {
    // A descriptive name shown in the k6 output.
    simultaneous_requests: {
      // Each virtual user runs the default function a fixed number of times.
      executor: "per-vu-iterations",
      // Simulate 80 clients starting this work concurrently.
      vus: 80,
      // Each of the 80 virtual users makes one request: 80 requests total.
      iterations: 1,
      // Stop the scenario if it cannot finish its requests within 30 seconds.
      maxDuration: "30s",
    },
  },
};

// The command can choose the route to compare, for example:
// ENDPOINT=sync-wait k6 run scripts/load/async-demo.js
// If ENDPOINT is absent, run the async route by default.
const endpoint = __ENV.ENDPOINT || "async-wait";

// k6 calls this function once for each configured virtual-user iteration.
export default function () {
  // Both routes wait for 0.25 seconds, so their concurrency behavior can be
  // compared without changing the simulated amount of I/O.
  const response = http.get(
    `http://localhost:8000/async-demo/${endpoint}?seconds=0.25`,
  );

  // A check records the result in the summary. It does not stop other virtual
  // users from running if this request fails.
  check(response, {
    "response is 200": (result) => result.status === 200,
  });
}
