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
- Command or test: docker compose -p barq-assessment logs nginx --tail=20 , 
- Actual output: connect() failed (111: Connection refused) while connecting to upstream
- Failed attempt and what changed your thinking: fixed wrong port in NGINX.conf file , still doesn't work
- Root cause: APPHOST was set in docker-compose.yml to 127.0.0.1 , making it unreachable from outside the network
- Fix: changed APPHOST from 127.0.0.1 to 0.0.0.0 to be reached from anywhere
- Retest evidence: " curl http://127.0.0.1:8080/" returned a welcome message
- Related commit: 72bb166 
- Remaining uncertainty: None

## Entry 4 / 9/9/2026 / 6:45pm
- Symptom: postgress and redis not available
- Hypothesis: connection settings dont match actual configuration
- Command or test:  curl http://127.0.0.1:8080/ready
- Actual output: 
	{"dependencies":{"postgres":"unavailable","redis":"unavailable"},"instance_id":"app-01","service":"barq-api","status":"not_ready","version":"2.0.0"}
- Failed attempt and what changed your thinking: none
- Root cause: typo in config/app.env and wrong default ports
- Fix: fixed the typo and wrote correct ports 
- Retest evidence: 'curl http://127.0.0.1:8080/ready' returns postgres and redis ready 
- Related commit:4db3da8
- Remaining uncertainty:None

## Entry 5 / 9/9/2026 / 7:32pm
- Symptom: /instance always returns "app-01" only even when there are multiple requests
- Hypothesis: INSTANCE ID of app-02 may not be set correctly
- Command or test:   curl -s http://127.0.0.1:8080/instance | python3 -c "import sys,json; print(json.load(sys.stdin)['instance_id'])"
- Actual output: always "app-01"
- Failed attempt and what changed your thinking:None
- Root cause: both instances have ID "app-01"
- Fix: change id of second instance to "app-02"
- Retest evidence: "curl -s http://127.0.0.1:8080/instance" returned both app-01 and app-02 
- Related commit: fa5c77a 
- Remaining uncertainty:None

## Entry 6 / 9/9/2026 / 8:19pm
- Symptom: new created records disappear after container restarts
- Hypothesis: volume may be incorrectly mounted
- Command or test: curl -s http://127.0.0.1:8080/records
- Actual output: the added record is not there
- Failed attempt and what changed your thinking: None
- Root cause: the mount volume in docker-compose.yml was set incorrectly to "- postgres-data:/var/lib/postgresql/backup" and 
- Fix: changed it to the correct "/var/lib/postgresql/data" and deleted the tmpfs gettting saved to RAM
- Retest evidence: "curl -s http://127.0.0.1:8080/records" returned added record even after container restart
- Related commit: 1f74e10 
- Remaining uncertainty: None

