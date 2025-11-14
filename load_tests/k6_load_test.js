/**
 * k6 Load Test Script for CEX/DEX Arbitrage Platform
 * 
 * Install k6: https://k6.io/docs/getting-started/installation/
 * Run: k6 run load_tests/k6_load_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const successfulRequests = new Counter('successful_requests');

// Test configuration
export const options = {
  stages: [
    // Ramp-up: 0 to 50 users over 1 minute
    { duration: '1m', target: 50 },
    
    // Steady state: 50 users for 3 minutes
    { duration: '3m', target: 50 },
    
    // Peak load: 50 to 150 users over 2 minutes
    { duration: '2m', target: 150 },
    
    // Peak steady: 150 users for 2 minutes
    { duration: '2m', target: 150 },
    
    // Stress test: 150 to 300 users over 1 minute
    { duration: '1m', target: 300 },
    
    // Stress steady: 300 users for 1 minute
    { duration: '1m', target: 300 },
    
    // Ramp-down: 300 to 0 users over 1 minute
    { duration: '1m', target: 0 },
  ],
  
  thresholds: {
    // 95% of requests should complete within 200ms
    'api_latency': ['p(95)<200'],
    
    // Error rate should be below 1%
    'errors': ['rate<0.01'],
    
    // HTTP failures should be below 1%
    'http_req_failed': ['rate<0.01'],
    
    // 95% of requests should complete within 500ms
    'http_req_duration': ['p(95)<500'],
  },
};

const BASE_URL = 'http://localhost:8001';

export default function() {
  // Simulate realistic user behavior
  
  // 1. Check system status (most common operation)
  {
    const res = http.get(`${BASE_URL}/api/v1/status`);
    const success = check(res, {
      'status is 200': (r) => r.status === 200,
      'has connections': (r) => JSON.parse(r.body).connections !== undefined,
    });
    
    errorRate.add(!success);
    apiLatency.add(res.timings.duration);
    if (success) successfulRequests.add(1);
  }
  
  sleep(1);
  
  // 2. Get opportunities (frequent operation)
  {
    const res = http.get(`${BASE_URL}/api/v1/opportunities?limit=50`);
    const success = check(res, {
      'status is 200': (r) => r.status === 200,
      'has opportunities array': (r) => JSON.parse(r.body).opportunities !== undefined,
    });
    
    errorRate.add(!success);
    apiLatency.add(res.timings.duration);
    if (success) successfulRequests.add(1);
  }
  
  sleep(2);
  
  // 3. Get trades (moderate frequency)
  {
    const res = http.get(`${BASE_URL}/api/v1/trades?limit=100`);
    const success = check(res, {
      'status is 200': (r) => r.status === 200,
      'has trades array': (r) => JSON.parse(r.body).trades !== undefined,
    });
    
    errorRate.add(!success);
    apiLatency.add(res.timings.duration);
    if (success) successfulRequests.add(1);
  }
  
  sleep(2);
  
  // 4. Get metrics (monitoring systems)
  {
    const res = http.get(`${BASE_URL}/api/metrics`);
    const success = check(res, {
      'status is 200': (r) => r.status === 200,
      'is prometheus format': (r) => r.body.includes('arb_'),
    });
    
    errorRate.add(!success);
    apiLatency.add(res.timings.duration);
    if (success) successfulRequests.add(1);
  }
  
  sleep(3);
}

export function handleSummary(data) {
  return {
    'load_test_results.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  let summary = '';
  
  summary += `${indent}\n`;
  summary += `${indent}Load Test Summary\n`;
  summary += `${indent}================\n`;
  summary += `${indent}\n`;
  summary += `${indent}Total Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `${indent}Failed Requests: ${data.metrics.http_req_failed.values.count}\n`;
  summary += `${indent}Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)}/s\n`;
  summary += `${indent}\n`;
  summary += `${indent}Response Time:\n`;
  summary += `${indent}  p50: ${data.metrics.http_req_duration.values['p(50)'].toFixed(2)}ms\n`;
  summary += `${indent}  p95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `${indent}  p99: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `${indent}\n`;
  summary += `${indent}Custom Metrics:\n`;
  summary += `${indent}  API Latency p95: ${data.metrics.api_latency.values['p(95)'].toFixed(2)}ms\n`;
  summary += `${indent}  Error Rate: ${(data.metrics.errors.values.rate * 100).toFixed(2)}%\n`;
  summary += `${indent}  Successful Requests: ${data.metrics.successful_requests.values.count}\n`;
  summary += `${indent}\n`;
  
  return summary;
}
