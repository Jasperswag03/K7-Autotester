# Automated K6 VU Testing

## Overview

This project automates the process of testing and validating Virtual User (VU) scalability with K6. The script runs tests to determine the maximum number of Virtual Users that a system can handle while maintaining performance thresholds. It gradually increases the VUs, runs tests, and validates if the system can handle the load before continuing to increase the VUs.

Additionally, the test script provided is designed for HTTP load testing, with adjustable configurations for ramp-up, load duration, and performance thresholds.

## Features

- **K6 Testing**: Run automated K6 tests with configurable VUs, duration, ramp-up time, and validation runs.
- **Automated Scaling**: Automatically increases VUs in each test until failure is detected, then validates the maximum stable VU count.
- **Thresholds and Validation**: Configurable thresholds for request errors and response times (e.g., HTTP request failures below 1%, and 95% of requests should be under 1000ms).
- **Customizable Configuration**: Multiple arguments to customize initial VUs, increments, validation runs, duration, and ramp-up time.

## Test Script Example

The accompanying `test-script.js` file is designed to test your HTTP endpoints with configurable ramp-up and constant load phases. Here’s an overview of how the script works:

### Configuration

javascript

Copy code

`import http from 'k6/http'; import { check, sleep } from 'k6';  // Environment variables for test configuration const target = __ENV.VUS || 300; const rampupTime = __ENV.RAMPUP || "5s"; const duration = __ENV.DURATION || "1m";  // K6 options for test scenarios export const options = {   scenarios: {     rampUp: {       executor: 'ramping-vus',       startVUs: 0,       stages: [           { duration: rampupTime, target: target }, // Ramp-up phase       ],       tags: { rampUp: 'true' },     },     instantLoad: {       executor: 'constant-vus',       vus: target,        duration: duration,       startTime: rampupTime,        tags: { rampUp: 'false' }, // Instant load phase     },   },   thresholds: {     // Performance thresholds to abort test on failure     'http_req_failed{rampUp:false}': [{ threshold: 'rate==0', abortOnFail: true }],      'http_req_duration{rampUp:false}': [{ threshold: 'p(95)<1000', abortOnFail: true }], // 95% requests < 1000ms   },   summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'], // Stats without ramp-up };  // Main function for the virtual user to execute export default function () {   // HTTP GET requests   http.get('http://localhost:3000/channel');   http.get('http://localhost:3000/channel/create');   sleep(1); // Simulate wait time between requests }`

### Key Parameters

- **VUS**: Number of virtual users to simulate during the test (default: 300).
- **RAMPUP**: Time to gradually increase the VUs (default: 5 seconds).
- **DURATION**: Duration of the test (default: 1 minute).
- **Thresholds**: Performance limits for HTTP requests:
    - Requests should not fail (rate=0).
    - 95% of requests should complete within 1000ms.

### Additional Setup for Authentication (Optional)

If your test requires JWT authentication, you can set up a login function to obtain the token:

javascript

Copy code

``export function setup() {   const loginHeaders = { 'Content-Type': 'application/json' };    const loginResponse = http.post('http://localhost/auth/login', JSON.stringify({     name: 'your_username',     password: 'your_password',   }), { headers: loginHeaders });    const isLoginSuccessful = check(loginResponse, {     'login successful': (res) => res.status === 200 && res.json('accessToken') !== undefined,   });    if (!isLoginSuccessful) {     throw new Error('Login failed');   }    return loginResponse.json('accessToken'); }  export default function (accessToken) {   // Use the accessToken for requests   const authHeaders = { Authorization: `Bearer ${accessToken}` };    http.get('http://localhost:3000/channel', { headers: authHeaders });   http.get('http://localhost:3000/channel/create', { headers: authHeaders });   sleep(1); }``

### HTTP Methods Supported

- **GET**: Fetch data from an endpoint.
- **POST**: Send data to an endpoint. E.g., login or create resources.
- **TRACE**: Not allowed in K6.

### Example of HTTP Request Usage:

javascript

Copy code

`// GET request: http.get('http://localhost/api/endpoint');  // POST request with JSON body: http.post('http://localhost/api/endpoint', JSON.stringify({ key: 'value' }), { headers: { 'Content-Type': 'application/json' } });`

### Running the Test

1. Clone or download the repository.
2. Install K6 by following the installation instructions on the K6 website.
3. Run the main Python script to execute the test process.
4. The script will handle the execution of K6 tests, incrementing the VUs, and validating the performance thresholds.
5. Check the console output for detailed logs on the test progress and results.

## Arguments

- `-vu, --initial_vus`: Initial number of virtual users.
- `-i, --increment`: The increment by which the VUs increase.
- `-vr, --validation_runs`: Number of validation runs for the maximum stable VU count.
- `-d, --delay_between_tests`: Delay (in seconds) between test runs.
- `-t, --duration`: Duration of each K6 test in seconds.
- `-rt, --rampup_time`: Ramp-up time in seconds.
- `-v, --verbose`: Enable verbose logging to see detailed K6 logs.
- `--k6_script`: Path to the K6 test script (default is `Scripts/test-script.js`).