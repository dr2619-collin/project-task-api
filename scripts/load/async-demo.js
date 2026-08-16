import http from "k6/http";
import { check } from "k6";

// Start the local FastAPI application before running this course demonstration.
// Each virtual user makes exactly one request concurrently.
export const options = {
  scenarios: {
    simultaneous_requests: {
      executor: "per-vu-iterations",
      vus: 80,
      iterations: 1,
      maxDuration: "30s",
    },
  },
};

const endpoint = __ENV.ENDPOINT || "async-wait";

export default function () {
  const response = http.get(
    `http://localhost:8000/async-demo/${endpoint}?seconds=0.25`,
  );

  check(response, {
    "response is 200": (result) => result.status === 200,
  });
}
