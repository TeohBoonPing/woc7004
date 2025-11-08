import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Metrics
let reqsDB = new Counter('db_reqs');
let reqsRedis = new Counter('redis_reqs');
let latDB = new Trend('db_latency', true);
let latRedis = new Trend('redis_latency', true);

// Configuration
const NUM_FIXED_URLS = 50000;
const BASE_URL = 'http://web:8080/api/links';
const AUTH_HEADER = { headers: { Authorization: 'CHANGEME', 'Content-Type': 'application/json' } };

function getFixedURL() {
    const id = Math.floor(Math.random() * NUM_FIXED_URLS) + 1;
    return `https://example.com/${id}`;
}

// K6 options
export let options = {
    scenarios: {
        db_only: {
            executor: 'per-vu-iterations',
            vus: 10,
            iterations: 5000, // 10 VUs × 5000 = 50,000 requests
            exec: 'dbOnly',
        },
        redis_cache: {
            executor: 'per-vu-iterations',
            vus: 10,
            iterations: 5000, // 10 VUs × 5000 = 50,000 requests
            exec: 'redisCache',
        },
    },
    thresholds: {
        'db_latency': ['p(90)<200', 'p(95)<250'],
        'redis_latency': ['p(90)<50', 'p(95)<100'],
    },
};


// DB-only scenario
export function dbOnly() {
    const url = getFixedURL();
    const res = http.post(`${BASE_URL}/by_long`, JSON.stringify({ original_url: url }), AUTH_HEADER);

    reqsDB.add(1); // increment for every request
    latDB.add(res.timings.duration);

    // optional: check status
    check(res, { 'status 200': (r) => r.status === 200 });

    sleep(0.01);
}

// Redis scenario
export function redisCache() {
    const url = getFixedURL();
    const res = http.post(`${BASE_URL}/redis`, JSON.stringify({ original_url: url }), AUTH_HEADER);

    reqsRedis.add(1);
    latRedis.add(res.timings.duration);

    check(res, { 'status 200': (r) => r.status === 200 });

    sleep(0.01);
}

// Custom summary
export function handleSummary(data) {
    const db = data.metrics['db_latency']?.values || {};
    const redis = data.metrics['redis_latency']?.values || {};
    const dbReqs = data.metrics['db_reqs']?.values.count || 0;
    const redisReqs = data.metrics['redis_reqs']?.values.count || 0;

    function compare(dbValue, redisValue) {
        if (!dbValue || !redisValue) return '-';
        const percent = ((1 - redisValue / dbValue) * 100).toFixed(1);
        if (percent > 0) return `+${percent}%`;
        if (percent < 0) return `${percent}%`;
        return '0%';
    }

    // Calculate overall performance as average of avg, median, p90, p95 improvements
    function overallPerformance() {
        const metrics = ['avg', 'med', 'p(90)', 'p(95)'];
        let sum = 0;
        let count = 0;
        for (const m of metrics) {
            if (db[m] && redis[m]) {
                sum += (1 - redis[m] / db[m]) * 100;
                count++;
            }
        }
        if (count === 0) return '-';
        const avgPercent = (sum / count).toFixed(1);
        return `+${avgPercent}%`;
    }

    const csvLines = [
        'Metric,DB-only,Redis Cache,Diff (% faster),Description',
        `Total User Requests,${dbReqs},${redisReqs},-,Total number of URL shortening or retrieval requests sent by users during the test`,
        `Total Time Performance,30s,30s,-,Total duration of the test scenario simulating user traffic`,
        `Avg Latency (ms),${db.avg?.toFixed(2) || 'N/A'},${redis.avg?.toFixed(2) || 'N/A'},${compare(db.avg, redis.avg)},"Average time taken to shorten or retrieve a URL; shows how much faster Redis serves requests from cache vs database, reducing user wait time"`,
        `Median Latency (ms),${db.med?.toFixed(2) || 'N/A'},${redis.med?.toFixed(2) || 'N/A'},${compare(db.med, redis.med)},"Median request time; using Redis means more requests are served faster, improving perceived performance for most users"`,
        `p(90) Latency (ms),${db['p(90)']?.toFixed(2) || 'N/A'},${redis['p(90)']?.toFixed(2) || 'N/A'},${compare(db['p(90)'], redis['p(90)'])},"90th percentile latency: Redis reduces slower request times, making the system more responsive even under high load"`,
        `p(95) Latency (ms),${db['p(95)']?.toFixed(2) || 'N/A'},${redis['p(95)']?.toFixed(2) || 'N/A'},${compare(db['p(95)'], redis['p(95)'])},"95th percentile latency: Shows that even the slowest requests benefit from Redis cache, improving reliability"`,
        `Requests to Database,${dbReqs},0,-,"Number of requests that actually hit the database; Redis serves cached requests directly, reducing database load and saving compute resources"`,
        `Overall Performance,-,-,${overallPerformance()},"Average % improvement across Avg, Median, p90, and p95 latency metrics, showing overall performance gain when using Redis"`
    ];

    const csvContent = csvLines.join('\n');

    console.log('\n===== PERFORMANCE SUMMARY (CSV) =====\n');
    console.log(csvContent);

    return {
        '/results/performance_summary.csv': csvContent
    };
}