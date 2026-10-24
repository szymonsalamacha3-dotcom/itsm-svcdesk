# Lab 4 Stretch 1 — independent second-investigator transcript

## Initial question

Checkout latency was paged at 2026-10-12T05:06:19Z. Investigate 2026-10-12T04:55:00Z through 2026-10-12T05:15:00Z. Compare relevant service behavior in that incident window against the five-minute baseline ending at 2026-10-12T04:56:00Z. Use only the read-only Prometheus endpoint `http://localhost:19090`.

## Queries and observed responses

All timestamps below are UTC. `query_range` evaluations use a five-minute `rate(...)` window and one-minute step unless noted. The listed concise outputs are the actual returned values, with epoch timestamps rendered as their equivalent UTC instants.

### 1. Prometheus target availability at the page time

**GET** `/api/v1/query?query=up&time=2026-10-12T05:06:19Z`

PromQL: `up`

Response: success; `up=1` for `alertmanager:9093`, `pager:8080`, `seeded-flagd:8080`, and `svcdesk:8080`.

### 2. Metric-name discovery over the incident window

**GET** `/api/v1/label/__name__/values?start=2026-10-12T04:55:00Z&end=2026-10-12T05:15:00Z`

This metadata response was 17.2 KB and not fully displayed by the command runner. I repeated the same timestamp-bounded metadata request and locally filtered the returned metric names. Relevant returned names included:

- App-specific: `demo_cart_add_item_latency_seconds_{bucket,count,sum}`, `demo_cart_get_cart_latency_seconds_{bucket,count,sum}`, `demo_payment_transactions_total`, `demo_shipping_items_shipped_total`.
- Request/RPC/span metrics: `http_server_request_duration_seconds_{bucket,count,sum}`, `rpc_client_call_duration_seconds_{bucket,count,sum}`, `rpc_server_call_duration_seconds_{bucket,count,sum}`, `traces_span_metrics_duration_milliseconds_{bucket,count,sum}`.
- Other discovered families included DB, HTTP-client, Redis, and PostgreSQL metrics. No metric name containing `checkout` was returned by the filtered name search.

A second call to that same metadata endpoint, with the same explicit UTC `start` and `end`, filtered application metric names and returned: `demo_ad_requests_total`, `demo_cart_add_item_latency_seconds_bucket/count/sum`, `demo_cart_get_cart_latency_seconds_bucket/count/sum`, `demo_exchange_conversions_counter_total`, `demo_notification_confirmations_total`, `demo_payment_transactions_total`, `demo_recommendation_requests_total`, and `demo_shipping_items_shipped_total`.

### 3. Request-count series and labels at the page time

**GET** `/api/v1/query?query=http_server_request_duration_seconds_count&time=2026-10-12T05:06:19Z`

PromQL: `http_server_request_duration_seconds_count`

Concise response excerpt (labels and counter values):

- `opentelemetry-demo/frontend`: GET 200 = 1710, GET 308 = 209, GET 500 = 3, POST 200 = 484.
- `opentelemetry-demo/cart`: `AddItem` POST 200 = 380, `EmptyCart` POST 200 = 127, `GetCart` POST 200 = 697.
- `opentelemetry-demo/shipping`: `/get-quote` POST 200 = 127, `/ship-order` POST 200 = 127.
- `svcdesk`: `/health` GET 200 = 1, `/tickets/{ticket_id}/ack` POST 200 = 1, `/tickets` POST 201 = 1.

### 4. Cart and instrumented HTTP server p95 trends

**GET** `/api/v1/query_range` with each PromQL below, `start=2026-10-12T04:56:00Z`, `end=2026-10-12T05:15:00Z`, `step=60s`:

1. `histogram_quantile(0.95, sum by (le) (rate(demo_cart_add_item_latency_seconds_bucket[5m])))`
2. `histogram_quantile(0.95, sum by (le) (rate(demo_cart_get_cart_latency_seconds_bucket[5m])))`
3. `histogram_quantile(0.95, sum by (service_name,le) (rate(http_server_request_duration_seconds_bucket{service_namespace="opentelemetry-demo"}[5m])))`

Concise response values at 04:56 / 05:06 / 05:11 / 05:15 UTC:

- App cart-add p95: 4.75 / 4.75 / 4.75 / 4.75 ms.
- App cart-get p95: 4.75 / 4.75 / 4.75 / 4.75 ms.
- HTTP server cart p95: 4.785 / 4.813 / 4.766 / 4.750 ms.
- HTTP server frontend p95: 40.17 / 49.11 / 35.63 / 36.73 ms.
- HTTP server shipping p95: 4.75 / 4.988 / 4.75 / 4.75 ms.

### 5. RPC and span metric dimensions around the page

**GET** `/api/v1/query?query=rpc_client_call_duration_seconds_count&time=2026-10-12T05:06:19Z`

PromQL: `rpc_client_call_duration_seconds_count`

The returned vector was large. Narrow follow-up queries at the same explicit timestamp showed:

**GET** `/api/v1/query?query=rpc_client_call_duration_seconds_count%7Bjob%3D%22opentelemetry-demo%2Fcheckout%22%7D&time=2026-10-12T05:06:19Z`

PromQL: `rpc_client_call_duration_seconds_count{job="opentelemetry-demo/checkout"}`

Response series (method, status, counter): Cart `EmptyCart` OK 119; Cart `GetCart` OK 119; Currency `Convert` OK 337; Payment `Charge` OK 119; ProductCatalog `GetProduct` OK 218.

**GET** `/api/v1/query?query=rpc_server_call_duration_seconds_count%7Bjob%3D%22opentelemetry-demo%2Fcheckout%22%7D&time=2026-10-12T05:06:19Z`

PromQL: `rpc_server_call_duration_seconds_count{job="opentelemetry-demo/checkout"}`

Response: checkout `oteldemo.CheckoutService/PlaceOrder`, status OK, counter 118.

**GET** `/api/v1/query?query=http_client_request_duration_seconds_count%7Bjob%3D%22opentelemetry-demo%2Ffrontend%22%7D&time=2026-10-12T05:06:19Z`

PromQL: `http_client_request_duration_seconds_count{job="opentelemetry-demo/frontend"}`

Response: two frontend series, to `metadata.google.internal.` and `169.254.169.254`, each counter 1.

**GET** `/api/v1/query?query=traces_span_metrics_duration_milliseconds_count&time=2026-10-12T05:06:19Z`

PromQL: `traces_span_metrics_duration_milliseconds_count`

This broad vector was too large to display in full. Focused timestamp-bounded follow-ups:

- `traces_span_metrics_duration_milliseconds_count{service_name="checkout"}` returned checkout spans including server `oteldemo.CheckoutService/PlaceOrder` (126), internal `prepareOrderItemsAndShippingQuoteFromCart` (126), and client spans for Cart `EmptyCart`/`GetCart` (126 each), Currency `Convert` (354), Payment `Charge` (126), ProductCatalog `GetProduct` (228), and `POST` (378).
- `traces_span_metrics_duration_milliseconds_count{service_name="cart"}` returned cart server spans `AddItem` (379), `EmptyCart` (126), `GetCart` (695), plus client spans to `valkey-cart:6379` (2080), flagd `ResolveBoolean` (42), and flagd `ResolveFloat` (126).

### 6. Checkout and dependency latency over the comparison interval

**GET** `/api/v1/query_range`, `start=2026-10-12T04:56:00Z`, `end=2026-10-12T05:15:00Z`, `step=60s`, separately for:

1. `histogram_quantile(0.95, sum by (rpc_method,le) (rate(rpc_server_call_duration_seconds_bucket{job="opentelemetry-demo/checkout"}[5m])))`
2. `histogram_quantile(0.95, sum by (rpc_method,le) (rate(rpc_client_call_duration_seconds_bucket{job="opentelemetry-demo/checkout"}[5m])))`
3. `sum by (service_name,http_response_status_code) (rate(http_server_request_duration_seconds_count{service_namespace="opentelemetry-demo"}[5m]))`

Key actual samples at 04:56 / 05:06 / 05:11 / 05:15 UTC:

- Checkout `PlaceOrder` RPC-server p95: 48.59 / 247.5 / 145 / 48.58 ms.
- Checkout client RPC p95 remained low. `EmptyCart`: 4.89 / 9.83 / 6.50 / 4.95 ms; `GetCart`: 4.89 / 4.75 / 4.75 / 4.75 ms; Currency `Convert`: 4.75 ms at all four samples; Payment `Charge`: 4.75 / 4.75 / 4.75 / 4.95 ms; ProductCatalog `GetProduct`: 4.75 / 4.87 / 4.75 / 4.75 ms.
- HTTP request rates showed frontend 500s at 05:06 (0.00833/s) and 05:11 (0.01250/s), returning to 0 at 05:15. Frontend 200 rate was 1.975 / 1.850 / 2.000 / 2.092 per second at the four samples. Cart and shipping 200s continued throughout.

### 7. Checkout/card span latency breakdown

**GET** `/api/v1/query_range`, `start=2026-10-12T04:56:00Z`, `end=2026-10-12T05:15:00Z`, `step=60s`, separately for:

1. `histogram_quantile(0.95, sum by (span_name,le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout"}[5m])))`
2. `histogram_quantile(0.95, sum by (span_name,le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="cart"}[5m])))`

Key actual p95 samples at 04:56 / 05:06 / 05:11 / 05:15 UTC, in milliseconds:

- Checkout server span `oteldemo.CheckoutService/PlaceOrder`: 48 / 5250 / 127.5 / 48.
- Checkout client spans: Cart `EmptyCart` 5.68 / 12 / 5.89 / 5.55; Cart `GetCart` 3.20 / 1.90 / 1.97 / 3.10; Currency `Convert` 1.90 throughout; Payment `Charge` 5.74 / 5.73 / 5.52 / 5.61; ProductCatalog `GetProduct` 3.92 / 5.08 / 3.97 / 3.96.
- Checkout internal `prepareOrderItemsAndShippingQuoteFromCart`: 47.88 / 47.89 / 47.85 / 47.65.
- Cart server spans `AddItem`: 1.94 / 1.90 / 1.96 / 1.92; `GetCart`: 1.91 / 1.90 / 1.90 / 1.91. Cart `EmptyCart` was 4.40 / 12 / 4.55 / 3.96. Cart Valkey client span stayed 1.90 throughout.

### 8. Additional checkout cross-checks

**GET** `/api/v1/query_range`, `start=2026-10-12T04:56:00Z`, `end=2026-10-12T05:15:00Z`, `step=60s`, for each:

1. `histogram_quantile(0.50, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder"}[5m])))`
2. `rate(traces_span_metrics_duration_milliseconds_sum{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder"}[5m]) / rate(traces_span_metrics_duration_milliseconds_count{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder"}[5m])`
3. `rate(rpc_server_call_duration_seconds_sum{job="opentelemetry-demo/checkout",rpc_method="oteldemo.CheckoutService/PlaceOrder"}[5m]) / rate(rpc_server_call_duration_seconds_count{job="opentelemetry-demo/checkout",rpc_method="oteldemo.CheckoutService/PlaceOrder"}[5m])`
4. `sum by (rpc_method,rpc_response_status_code) (rate(rpc_client_call_duration_seconds_count{job="opentelemetry-demo/checkout"}[5m]))`

Key outputs at 04:56 / 05:06 / 05:11 / 05:15 UTC:

- Checkout PlaceOrder span p50: 30 / 79.69 / 58.33 / 30 ms.
- PlaceOrder span mean: 30.19 / 339.11 / 56.21 / 31.27 ms.
- RPC server PlaceOrder mean: 30.30 / 315.29 / 52.52 / 31.55 ms.
- Checkout client RPC response statuses shown were all `OK`; rates stayed active (e.g. Cart EmptyCart 0.1458 / 0.0917 / 0.1167 / 0.1042 per second; Payment Charge the same respective rates).

For completeness, two one-off availability/resource checks returned empty vectors at 2026-10-12T05:06:19Z:

- `process_cpu_seconds_total{job="opentelemetry-demo/checkout"}`
- `container_cpu_usage_seconds_total{container_label_com_docker_compose_service="checkout"}`

## Independent hypotheses

1. **Most likely: a transient checkout-service handling/tail-latency problem, in work not explained by the observed child RPC calls.** The checkout `PlaceOrder` trace p95 rose from 48 ms at the 04:56 baseline to 5.25 seconds at 05:06, while its preparatory internal span stayed near 48 ms and its measured Cart, Currency, Payment, and ProductCatalog client spans stayed in the low single-digit milliseconds. The PlaceOrder mean also rose from about 30 ms to 339 ms in trace metrics (about 315 ms in RPC-server metrics), then moved back toward baseline by 05:15. This supports checkout-local or otherwise uninstrumented waiting/processing; the available metrics do not identify the specific mechanism.
2. **Less likely as primary cause: a downstream Cart/Payment/Currency/ProductCatalog outage.** Their measured checkout client calls remained successful (`OK`) and low-latency in the sampled windows. Cart had small transient increases in `EmptyCart` and flagd `ResolveFloat` spans, but its `GetCart`, `AddItem`, and Valkey spans stayed near baseline; those increases do not match the 5.25-second PlaceOrder tail.
3. **Caveat / possible co-symptom:** frontend 500s appeared at low rates during part of the window (3 observed at page time; nonzero rates at 05:06 and 05:11). These data do not establish that they caused checkout latency. Also, trace-derived PlaceOrder p95 (5.25 s) and RPC histogram-derived p95 (247.5 ms) differ substantially at 05:06, although the two means agree on a several-fold increase. I would treat the tail-size estimate cautiously and seek trace-level exemplars or additional instrumentation before naming an exact root cause.

### 9. Exact incident-start sample (follow-up)

To include the 04:55:00Z boundary itself, I repeated targeted range queries with `start=2026-10-12T04:55:00Z`, `end=2026-10-12T05:15:00Z`, `step=60s`:

1. `histogram_quantile(0.95, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder"}[5m])))`
2. `rate(traces_span_metrics_duration_milliseconds_sum{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder"}[5m]) / rate(traces_span_metrics_duration_milliseconds_count{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder"}[5m])`
3. `sum by (service_name,http_response_status_code) (rate(http_server_request_duration_seconds_count{service_namespace="opentelemetry-demo"}[5m]))`

Actual selected outputs at 04:55 / 04:56 / 05:06 / 05:11 / 05:15 UTC:

- PlaceOrder trace p95: 48 / 48 / 5250 / 127.5 / 48 ms.
- PlaceOrder trace mean: 29.43 / 30.19 / 339.11 / 56.21 / 31.27 ms.
- HTTP 500 rate for frontend: no returned series at 04:55 or 04:56; 0.00833 / 0.01250 / 0 per second at 05:06 / 05:11 / 05:15.
- At 04:55 the 200 rates were cart 1.0375/s, frontend 1.9375/s, shipping 0.25/s; these remained in comparable ranges through the sampled incident and recovery points.
