# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry / date / time
- Symptom:
- Hypothesis:
- Command or test:
- Actual output:
- Failed attempt and what changed your thinking:
- Root cause:
- Fix:
- Retest evidence:
- Related commit:
- Remaining uncertainty:

Do not fabricate a failed attempt just to fill the template. Record actual attempts.

## Entry 1 / 8/9/2026 / 5:18pm
- Symptom:trying to curl http://127.0.0.1:8080/ doesnt work , no response from NGINX 
- Hypothesis:listening port is probably wrong
- Command or test: curl http://127.0.0.1:8080/
- Actual output:
	curl: (56) Recv failure: Connection reset by peer
- Failed attempt and what changed your thinking: None
- Root cause:: Port mismatch ,docker was forwarding traffic to port 81 but NGINX was listening on port 80
- Fix:changed port in docker-compose.yml from :81 to :80 and remover local host binding
- Retest evidence:ran again  curl http://127.0.0.1:8080/ and got bad gateway 502 instead of no connection
- Related commit: 8c8d6ed 
- Remaining uncertainty:NGINX still getting 502 error 


## Entry 2 / 9/9/2026 / 5:00pm
- Symptom:Docker compose shows app-01 and app-02 unhealthy 
- Hypothesis: health checker failing or chcking the wrong URL
- Command or test: docker compose -p barq-assessment ps -a
- Actual output:
NAME       IMAGE                                 COMMAND                  SERVICE    CREATED              STATUS                          PORTS
app-01     barq-assessment-app-01                "python -m app.server"   app-01     About a minute ago   Up About a minute (unhealthy)   8080/tcp
app-02     barq-assessment-app-02                "python -m app.server"   app-02     About a minute ago   Up About a minute (unhealthy)   8080/tcp

- Failed attempt and what changed your thinking: None
- Root cause: typo in docker-compose.yml , url checks for /healthz buut the correct route in flask app file is /health
- Fix: fixed the typo
- Retest evidence: 'docker compore ps -a' returned app-01 and app-02 as healthy
- Related commit:180cb6c
- Remaining uncertainty:NGINX still returning 502 


## Entry 3 / 9/9/2026 / 5:41pm
- Symptom:NGINX returning 502 bad gateway
- Hypothesis: NGINX listening on wrong port
- Command or test: docker compose -p barq-assessment logs nginx --tail=20
- Actual output: connect() failed (111: Connection refused) while connecting to upstream
- Failed attempt and what changed your thinking:fixed wrong port in NGINX.conf file , still doesn't work
- Root cause:
- Fix:
- Retest evidence:
- Related commit:
- Remaining uncertainty:

