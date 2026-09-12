# Security and production-readiness review

Record at least 8 concrete risks or improvements relevant to your final solution.
This is a review requirement, not the number of hidden faults.

## 1. Secrets
- Risk and evidence: hardcoded database password in config/app.env and pushed it to git
- Impact: anyone who can see the github repo can get the password and access the database
- Implemented fix / commit: used github secrets for the ci.yml pipeline so it doesnt leak the password in the action logs
- Production follow-up: use aws secrets manager or hashicorp vault to inject secrets at runtime instead of saving them in .env files
- How to verify: check github actions logs and see the password is hidden as ***

## 2. Ports
- Risk and evidence: postgres and redis ports 15432 and 16379 were published in docker-compose.yml 
- Impact: attackers could try to login to the database directly from the internet
- Implemented fix / commit: removed the ports block from postgres and redis completely so they cant be reached from the host machine
- Production follow-up: put databases in private subnets with strict firewalls so they have no public ip at all
- How to verify: run `docker port postgres` and make sure it returns nothing

## 3. Container user
- Risk and evidence: dockerfile was set to run as the root user by default
- Impact: if an attacker finds a bug in the app and gets inside the container , they have full admin rights
- Implemented fix / commit: changed USER to "app" in the dockerfile so it runs with low privileges 
- Production follow-up: enforce a read-only root filesystem in kubernetes so even if they get in they cant install malware
- How to verify: run `docker exec app-01 whoami` and see it says "app" not "root"

## 4. Image selection
- Risk and evidence: standard images like ubuntu are big and have lots of extra tools installed
- Impact: larger attack surface because there are more packages that might have vulnerabilities
- Implemented fix / commit: kept the alpine base images that were provided for nginx postgres and redis because they are already minimal and secure
- Production follow-up: use automated image scanning like trivy in the ci pipeline to block images with known security flaws
- How to verify: check the image tags in docker-compose.yml to see they all end in -alpine

## 5. Networks
- Risk and evidence: nginx could talk directly to the databases if it was on the same network
- Impact: if nginx gets hacked , the attacker can reach the database directly and steal data
- Implemented fix / commit: separated networks into frontend and backend , put databases only on backend and nginx only on frontend
- Production follow-up: implement strict network policies in kubernetes so only the app pods are physically allowed to talk to the database pods
- How to verify: run `docker exec nginx sh -c "ping postgres"` and see it fails to reach it

## 6. Persistence/backup
- Risk and evidence: restoring a bad backup could wipe out the real database
- Impact: total data loss if the backup script drops the database and then tries to load an empty sql file
- Implemented fix / commit: wrote restore.sh to load the backup into a temp database first and check if it worked before dropping the real one
- Production follow-up: use continuous backup tools like pgbackrest instead of simple sql dumps for point in time recovery
- How to verify: try to run restore.sh with an empty text file and see the script block it from touching the real database

## 7. Logging/monitoring
- Risk and evidence: we dont know when the database is getting overloaded until it crashes completely (like the timeout errors we saw at 11:25)
- Impact: long downtimes because we only react after the app goes offline and customers complain
- Implemented fix / commit: none implemented locally right now , just relying on standard docker logs and validate.py script
- Production follow-up: set up prometheus and grafana to track cpu usage and send slack alerts before it crashes
- How to verify: check `docker logs app-01` manually for errors

## 8. Availability
- Risk and evidence: NGINX wasn't retrying requests when one of the app containers crashed
- Impact: customers see 502 bad gateway errors when one backend goes down , even if the other one is working perfectly fine
- Implemented fix / commit: added proxy_next_upstream to nginx.conf so it fails over automatically to the working app
- Production follow-up: run apps in multiple aws availability zones and use a real cloud load balancer instead of just docker compose
- How to verify: stop app-02 and send a request to localhost:8080 and see that it still works through app-01
