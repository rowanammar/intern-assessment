# Evidence and submission index

- Repository URL: https://github.com/rowanammar/intern-assessment
- Final commit: 3b204d7
- Matching CI run: https://github.com/rowanammar/intern-assessment/actions/runs/34843378232
- Continuous 12-18 minute video URL: https://drive.google.com/file/d/12tJojInR5GGz9woEsKntakiaTsW8rAVx/view?usp=sharing
- Challenge receipt ID: 8b19163bfbdd4cd3b9eb754db88c6dce
- Starting video commit: 470248e 
- Later documentation-only commits, if any:
  I added this evidence index file.
  Also, note on a post-video code commit: during the very last step in the video where I was adding app-03, I accidentally made a YAML indentation error (indented by 4 spaces instead of 2). This made `docker compose up` fail and throw an error, so I commited and ended the video there early before running the final validation script. Following the "honest technical failure" rule, I left the video as-is showing the error, but I fixed the YAML indentation immediately after so the GitHub code runs perfectly with the 3 instances on port 8090 as requested.

## Requirement Mapping

- **Build/start stopped environment and show health**
  -> `docker compose up -d --build` -> commit: 470248e -> video timestamp: [00:19]
- **Test all endpoints (/, /health, /ready, /records, /counter)**
  -> terminal curl outputs -> commit: 470248e-> video timestamp: [00:50]
- **Prove both backends serve via NGINX**
  -> `/instance` curl alternating -> commit: 470248e-> video timestamp: [01:40]
- **Stop one backend, show traffic continues, recover it**
  -> `docker stop app-02` and failover -> commit: 470248e-> video timestamp: [01:50]
- **Created record survives container recreation**
  -> postgres-data volume persistence -> commit: 470248e-> video timestamp: [02:36]
- **Run validation and failure test**
  -> `validate.py` and `failure_test.py` passing -> commit: 470248e-> video timestamp: [03:35]
- **Historical log finding**
  -> grep on access.log showing 502s -> commit: 470248e-> video timestamp: [04:20]
- **Run video_challenge.sh and fix the fault**
  -> repaired network/pause state without compose down -> commit: 470248e-> video timestamp: [05:45]
- **Change port 8080 to 8090 live**
  -> modified `.env` and NGINX recreate -> commit:  cdcaf61 -> video timestamp: [08:07]
- **Add third app instance live**
  -> modified `docker-compose.yml` and `nginx.conf` -> commit:   cdcaf61 (fixed post-video) -> video timestamp: [09:07] 
