# Nginx Standards

Conventions for Nginx as reverse proxy / load balancer over the FastAPI replicas.

1. **Explicit upstream with `least_conn`.** Better than round-robin for variable-latency
   endpoints:
   ```nginx
   upstream cart_api {
     least_conn;
     server api1:8000 max_fails=3 fail_timeout=10s;
     server api2:8000 max_fails=3 fail_timeout=10s;
     keepalive 32;
   }
   ```
2. **Forward the right headers.** So the backend can do real-IP and HTTPS-aware logic:
   ```nginx
   proxy_set_header Host $host;
   proxy_set_header X-Real-IP $remote_addr;
   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   proxy_set_header X-Forwarded-Proto $scheme;
   proxy_http_version 1.1;
   proxy_set_header Connection "";
   ```
   The last two lines enable upstream keep-alives.
3. **Explicit timeouts that match the backend.**
   ```nginx
   proxy_connect_timeout 5s;
   proxy_send_timeout 30s;
   proxy_read_timeout 30s;
   ```
   The default 60s is too long for a checkout API and masks slow-query problems.
4. **Health route + compose healthcheck.**
   ```nginx
   location = /healthz {
     proxy_pass http://cart_api/healthz;
     access_log off;
   }
   ```
   FastAPI implements `/healthz` (returns 200 immediately) and `/readyz` (pings DB and
   Redis). Compose `healthcheck:` runs against `/healthz`.
5. **Gzip JSON, cap body size.**
   ```nginx
   gzip on;
   gzip_types application/json;
   gzip_min_length 512;
   client_max_body_size 1m;
   ```
   A checkout API has no reason to accept multi-megabyte bodies; capping early defends
   against trivial DoS.
