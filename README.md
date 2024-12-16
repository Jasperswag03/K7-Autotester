# Automated K6 Load Testing with Virtual Users

This repository provides a K6 test script designed to automate load testing for HTTP-based systems. It allows you to simulate multiple virtual users (VUs), gradually ramp up the load, and evaluate system performance based on defined thresholds.

## Table of Contents

1. [Overview](#overview)
2. [Test Script](#test-script)
3. [Configuration Options](#configuration-options)
4. [Authentication Setup (Optional)](#authentication-setup-optional)
5. [Running the Test](#running-the-test)
6. [Thresholds and Validation](#thresholds-and-validation)
7. [Endpoints Supported](#endpoints-supported)

---

## Overview

The system runs K6 load tests with two primary phases:

1. **Ramp-Up Phase**: Virtual users are gradually increased.
2. **Instant Load Phase**: A constant load of VUs is maintained.

The tests also validate that performance thresholds are met and ensure that the system can handle the specified load without issues.

---

## Test Script

The main test script (`test-script.js`) simulates virtual users (VUs) performing HTTP GET requests. The script is designed with two load phases and uses K6's `ramping-vus` and `constant-vus` executors to control how VUs are scaled.

Here’s an example of the script:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

// Configuration for virtual users, ramp-up, and test duration
const target = __ENV.VUS || 300;
const rampupTime = __ENV.RAMPUP || "5s";
const duration = __ENV.DURATION || "1m";

export const options = {
  scenarios: {
    rampUp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [{ duration: rampupTime, target: target }],
      tags: { rampUp: 'true' },
    },
    instantLoad: {
      executor: 'constant-vus',
      vus: target,
      duration: duration,
      startTime: rampupTime,
      tags: { rampUp: 'false' },
    },
  },
  thresholds: {
    'http_req_failed{rampUp:false}': [{ threshold: 'rate==0', abortOnFail: true }],
    'http_req_duration{rampUp:false}': [{ threshold: 'p(95)<1000', abortOnFail: true }],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'],
};

// Main function executed by each virtual user
export default function () {
  http.get('http://localhost:3000/channel');
  http.get('http://localhost:3000/channel/create');
  sleep(1); // Simulate time between requests
}
```

---

## Configuration Options

The script allows you to configure various options via environment variables:

- **VUS (Virtual Users)**: Number of virtual users to simulate (default: 300).
- **RAMPUP**: Duration for gradually increasing virtual users (default: 5s).
- **DURATION**: Total duration of the constant load phase (default: 1m).

### Example Command to Run the Test:
```bash
VUS=500 RAMPUP=10s DURATION=2m k6 run test-script.js
```

---

## Authentication Setup (Optional)

If your test requires JWT authentication, you can set up the login flow as follows:

```javascript
export function setup() {
  const loginHeaders = { 'Content-Type': 'application/json' };

  const loginResponse = http.post('http://localhost/auth/login', JSON.stringify({
    name: 'your_username',
    password: 'your_password',
  }), { headers: loginHeaders });

  const isLoginSuccessful = check(loginResponse, {
    'login successful': (res) => res.status === 200 && res.json('accessToken') !== undefined,
  });

  if (!isLoginSuccessful) {
    throw new Error('Login failed');
  }

  return loginResponse.json('accessToken');
}

export default function (accessToken) {
  const authHeaders = { Authorization: `Bearer ${accessToken}` };

  http.get('http://localhost:3000/channel', { headers: authHeaders });
  http.get('http://localhost:3000/channel/create', { headers: authHeaders });
  sleep(1);
}
```

---

## Running the Test

1. Install K6 by following the official installation guide.
2. Set the required environment variables:
    - `VUS`: Virtual users to simulate.
    - `RAMPUP`: Time to gradually increase virtual users.
    - `DURATION`: Duration of the constant load phase.
3. Run the K6 script with the following command:
    `k6 run test-script.js`
4. Check the K6 output for detailed logs, test progress, and results.

---

## Thresholds and Validation

The following performance thresholds are defined for validation:

- **HTTP request failures**: The failure rate should be 0% (`rate==0`).
- **HTTP request duration**: 95% of requests should complete within 1000ms (`p(95)<1000`).

If the thresholds are exceeded, the test will be aborted.

---

## Endpoints Supported

- **GET** requests are supported for fetching data (e.g., `/channel`, `/channel/create`).
- **POST** requests are supported with JSON bodies (e.g., for authentication).

The **TRACE** method is not supported in K6.