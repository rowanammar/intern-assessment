# AI usage disclosure

Write None if no AI was used. Otherwise record each use:

I used Antigravity as a fast search engine to help me find commands and syntax , especially for REGIX parts, quickly instead of googling everything , but i tested and verified all the work myself.

## Use 1: debugging docker network issues
- Tool/model: Antigravity
- Purpose: helping me figure out why NGINX was giving 502 bad gateway
- Files or decisions affected: docker-compose.yml , nginx.conf
- What you changed or rejected: it gave me a few reasons why it might be broken but i had to test them myself to find the real issue which was APP_HOST set to 127.0.0.1
- How you independently verified it: ran curl commands every time i changed something until i got a 200 ok
- Related commit: 72bb166

## Use 2: log analysis commands
- Tool/model: Antigravity
- Purpose: finding the right jq and grep commands to parse the json logs faster
- Files or decisions affected: log_analysis.md
- What you changed or rejected: the standard jq commands it gave me crashed because the access.log had a broken line at 313 , so i stopped using jq and switched to grep so it doesnt crash on bad json
- How you independently verified it: ran all the grep commands myself 
- Related commit: log analysis commits

## Use 3: python test scripts
- Tool/model: Antigravity
- Purpose: getting the basic python code structure for validate.py and failure_test.py
- Files or decisions affected: validate.py , failure_test.py
- What you changed or rejected: read through the code to make sure it actually hits the specific routes like /ready and /counter like the instructions asked
- How you independently verified it: ran them locally and watched them pass , also ran them in the github actions ci pipeline
- Related commit: validate.py commits

## Use 4: backup and restore scripts
- Tool/model: Antigravity
- Purpose: getting the correct syntax for pg_dump and psql inside docker
- Files or decisions affected: backup.sh , restore.sh
- What you changed or rejected: the first restore script it gave me was dangerous because it dropped the real database right away. i asked it to make a safer one that restores to a temp database first
- How you independently verified it: i created a record, deleted the containers with -v to delete the volumes then brought them up and restored the backup to see if the record came back
- Related commit: backup and restore commits

## Use 5: docs and formatting
- Tool/model: Antigravity
- Purpose: formatting my notes for decisions.md and security_review.md so they fit the requested template
- Files or decisions affected: decisions.md , security_review.md
- What you changed or rejected: made sure it only included things i actually did 
- How you independently verified it: checked my own docker-compose.yml and git history to make sure the evidence is accurate
- Related commit: docs commits

## Use 6: architecture diagram
- Tool/model: Antigravity
- Purpose: generating the architecture diagram from my docker-compose setup
- Files or decisions affected: architecture.drawio , architecture.png
- What you changed or rejected: I gave it my docker-compose file to draw the diagram for me, then I checked the picture to make sure it actually shows the frontend and backend networks correctly and exported it to png
- How you independently verified it: compared the picture to my own docker-compose.yml to make sure all the ports and health checks match what i actually built
- Related commit: architecture diagram commit
