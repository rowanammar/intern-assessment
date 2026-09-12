# Technical decisions

## Decision 1: Networks
- Choice: Put postgres and redis on backend network only and removed published ports
- Why: so they can't be reached from the host machine or from NGINX directly for better security
- Alternative: Placing all containers on a single default network and publishing database ports to `0.0.0.0`
- Trade-off: makes it harder to debug locally because I have to use docker exec instead of a GUI
- Evidence / commit: networks block in docker-compose.yml
- Production improvement: In a cloud enviroment , we can put databases in private subnets with strict security groups so they have no internet access at all

## Decision 2: Health checks
- Choice: used /health for the docker compose healthcheck instead of /ready
- Why: To avoid restarting the app just because redis is slow or unavailable , /health just checks if the flask app itself is running
- Alternative: using /ready for the healthcheck
- Trade-off: docker will say the container is "healthy" even if its returning 503 errors because the database is down, but it stops the container from crashing in a loop
- Evidence / commit: healthcheck test line in docker-compose.yml
- Production improvement: in an enviroment with kubernetes, use /health for liveness to restart the pod and /ready for readiness to stop sending traffic

## Decision 3: Timeouts and retries
- Choice: turned on proxy_next_upstream in NGINX so it retries on error or timeout or 502/503
- Why: so if app-02 crashes , the customer doesnt see an error page and the request just goes to app-01 instead automatically
- Alternative: leaving proxy_next_upstream off
- Trade-off: retrying requests takes more time , if the database is locked up then trying the second app will just waste resources and eventually timeout anyway
- Evidence / commit: nginx.conf file proxy settings
- Production improvement: use circuit breakers to stop sending traffic to dead backends entirely instead of trying over and over

## Decision 4: Restart and resource settings
- Choice: set cpu limits to 0.50 and memory to 128M/256M and used restart: unless-stopped
- Why: to stop one container with a memory leak from using all the RAM and crashing the whole server
- Alternative: not setting any limits and using restart: always
- Trade-off: if the app uses too much memory it will get killed instantly by the system instead of just running slow , and unless-stopped means i have to manually start it if i stopped it on purpose
- Evidence / commit: deploy resources limits in docker-compose.yml
- Production improvement: set up prometheus alerts to warn me when memory hits 80% before it actually crashes

## Decision 5: Base image
- Choice: kept the provided alpine versions for postgres redis and NGINX instead of changing them
- Why: the images are way smaller so they download faster and are more secure because they have less packages installed to exploit
- Alternative: changing them to the full normal images like ubuntu or debian
- Trade-off: alpine doesnt have some normal tools like bash or curl installed by default so debugging inside the container is harder
- Evidence / commit: image tags in docker-compose.yml
- Production improvement: use distroless images and scan them for vulnerabilities in the CI pipeline automatically

## Decision 6: Storage and restore scripts
- Choice: made restore.sh load the backup into a temp database first to check it before dropping the real one
- Why: if the backup file is empty or corrupted it wont accidentally delete the real working database
- Alternative: just dropping the real database right away and loading the backup
- Trade-off: needs more storage space while restoring because it holds two databases at the same time for a minute
- Evidence / commit: restore.sh file logic
- Production improvement: use point in time recovery instead of just sql dumps

## Decision 7: CI/CD secrets
- Choice: used github secrets to pass the postgres password into the ci.yml pipeline
- Why: to hide the database password so it doesnt show up in the git history for everyone to see
- Alternative: just hardcoding the password in the ci.yml file
- Trade-off: takes more time to set up because i have to go to github settings and add the secret manually before the pipeline works
- Evidence / commit: ci.yml file where it echos the secret into the .env file
- Production improvement: use AWS secrets manager to inject the password at runtime instead of saving it in a .env file
