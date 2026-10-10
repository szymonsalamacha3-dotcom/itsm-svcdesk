<!-- ai-generated: 80% - Copilot explained the measured proxy/client-server latency gap using the Lab 3 run output -->
# Client/server latency gap

The 100 ms downstream latency toxic with 10 ms jitter delayed responses after `svcdesk` had finished its work. In the same 60-second open-loop run, the client p99 was 289.7 ms and the service histogram p99 was 183.9 ms, leaving a measured gap of 105.8 ms. This is close to the injected delay, as expected: the server histogram stops when the application produces its response, while the client includes time spent in Toxiproxy forwarding that response.

The values are percentiles measured independently across requests, not a per-request subtraction, so their difference need not equal exactly 100 ms. Jitter, scheduling and the tail distribution affect each p99; latency correction also includes time from each scheduled request rather than hiding time waiting for a connection. The gap therefore shows the extra downstream time visible to callers but absent from the server-side request-duration histogram.
