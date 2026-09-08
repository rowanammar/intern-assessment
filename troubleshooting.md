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
- Symptom:Docker compose shows app-01 and app-02 unhealthy , trying to curl http://127.0.0.1:8080/ doesnt work , no response from NGINX 
- Hypothesis:listening port is probably wrong
- Command or test: docker compose -p barq-assessment ps -a  and   curl http://127.0.0.1:8080/
- Actual output:
NAME       IMAGE                                                                                        COMMAND                  SERVICE    CREATED              STATUS                          PORTS
app-01     barq-assessment-app-01                                                                       "python -m app.server"   app-01     About a minute ago   Up About a minute (unhealthy)   8080/tcp
app-02     barq-assessment-app-02                                                                       "python -m app.server"   app-02     About a minute ago   Up About a minute (unhealthy)   8080/tcp

curl: (56) Recv failure: Connection reset by peer

- Failed attempt and what changed your thinking:
- Root cause:
- Fix:
- Retest evidence:
- Related commit:
- Remaining uncertainty:
