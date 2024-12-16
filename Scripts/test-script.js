import http from 'k6/http';
import { check, sleep } from 'k6';


const target = __ENV.VUS || 300;
const rampupTime = __ENV.RAMPUP || "5s";
const duration = __ENV.DURATION || "1m";

export const options = {
  scenarios: {
    rampUp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
          { duration: rampupTime, target: target },
      ],
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
    'http_req_failed{rampUp:false}': [{ threshold: 'rate==0', abortOnFail: true }], // HTTP errors should be less than 1%, aborts test
    'http_req_duration{rampUp:false}': [{ threshold: 'p(95)<1000', abortOnFail: true }], // 95% of requests should be below 400ms
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'], // Exclude rampUp from summary stats
};



//endpoints should look like:
//GET: 
// http.get('http://baseurl/enpoint');

//POST:
// http.post('http://baseurl/enpoint', JSON.stringify({ key: 'value' }), { headers: { 'Content-Type': 'application/json' } });

//only TRACE is not allowed in k6.

//when in need of JWT token in request header:

//add accessToken to the arguments of  the default function:

//export default function (accessToken) {

// add this script:

//export function setup() {

// const loginHeaders = {
//   'Content-Type': 'application/json',
// };
// 
// const loginResponse = http.post('http://basurl/auth/login', JSON.stringify({name: 'value', password: 'value'}), { headers: { 'Content-Type': 'application/json' } });
// 
// const isLoginSuccessful = check(loginResponse, {
//   'login successful': (res) => res.status === 200 && res.json('accessToken') !== undefined,
// });
//
// if (!isLoginSuccessful) {
//   throw new Error('Login failed');
// }
//
// return loginResponse.json('accessToken'); 
// }


// Main function executed by each VU
export default function () {

  http.get('http://localhost:3000/channel');

  http.get('http://localhost:3000/channel/create');

  sleep(1);
}
