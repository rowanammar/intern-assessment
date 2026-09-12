# Log analysis

Use all three supplied logs. Answer every question with commands/scripts and actual output.

1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?

## Timeline
	First request was made at 11:00:00.015Z and the last request was made 11:29:57.578Z , so the time span is roughly 30 minutes
## Commands / scripts
	head -1 logs/access.log , tail -1 logs/access.log    	    	  	   to check timeline
	wc -l logs/access.log logs/application.log logs/error.log   		   to count lines
	jq empty logs/access.log , q empty logs/application.log     		   to find malformed lines
	grep -o 'lab-[0-9]*' logs/access.log | sort | uniq -d | wc -l		   to count duplicated lines
## Results	 
	total line count of each file:
		726   logs/access.log
   	 	730   logs/application.log
    	 	68    logs/error.log
	total valid lines :
		725   logs/access.log
   		729   logs/application.log
	total malformed lines :
		 1    logs/access.log
   		 1    logs/application.log
	total duplicated lines :
		 5    logs/access.log
   		49    logs/application.log

2. How many distinct client requests occurred? How did you deduplicate and avoid counting retries twice?

## Commands / scripts
	"grep "request_id" logs/access.log | grep -o 'lab-[0-9]*' | sort -u | wc -l"
 	To deduplicate I got each request ID and sorted them with sort -u to keep unique entries only , then counted those entries with wc -l
## Results	 
	total distinct requests: 720

3. What are the final client status counts and error rate? State your denominator.

## Commands / scripts
	grep -o '"status":[0-9]*' logs/access.log | sort | uniq -c | sort -rn
## Results	 
	620   "status":200
	47    "status":503
	40    "status":502
	10    "status":404
	8     "status":504
## Conclusions and limits
	Error rate: 14.5% (105 errors / 725 valid lines)
	Denominator: All valid and parseable lines in access.log	
4. Which paths, time windows and backends account for the failures?

## Commands / scripts
	grep '"status":[45]' logs/access.log | grep -o '"path":"/[a-z]*"' | sort | uniq -c | sort -rn	to find which paths failed
	grep '"status":[45]' logs/access.log | grep -o '2026-08-20T11:[0-9][0-9]' | sort | uniq -c	to find failure time windows
	grep '"status":[45]' logs/access.log | grep -o '"upstream":"[^"]*"' | sort | uniq -c		to find which backend failed
## Results
	Which paths failed:	 
		26 "path":"/records"
		26 "path":"/counter"
		23 "path":"/ready"
		10 "path":"/missing"
		10 "path":"/health"
		10 "path":"/"
	Failure time windows:
		1 2026-08-20T11:00
		1 2026-08-20T11:03
		8 2026-08-20T11:05
		9 2026-08-20T11:06
		8 2026-08-20T11:07
		8 2026-08-20T11:08
		9 2026-08-20T11:09
		8 2026-08-20T11:12
		8 2026-08-20T11:13
		8 2026-08-20T11:14
		8 2026-08-20T11:15
		1 2026-08-20T11:16
		1 2026-08-20T11:19
		8 2026-08-20T11:20
		8 2026-08-20T11:21
		1 2026-08-20T11:23
		4 2026-08-20T11:25
		5 2026-08-20T11:26
		1 2026-08-20T11:29	
	Backend failure:
		32 "upstream":"172.23.0.11:8080"
		73 "upstream":"172.23.0.12:8080"		
## Conclusions and limits
	system had multiple outages spiking specifically at minutes 05-15 and 20-26 , app-02 was responsible for most of the failures

5. What are the median and p95 client latencies? State the percentile method and units.

## Commands / scripts
	jq -R 'fromjson? | select(.request_time != null) | .request_time' logs/access.log | sort -n | python3 -c "
		import sys
		times = [float(x) for x in sys.stdin]
		times.sort()
		n = len(times)
		print(f'Median: {times[n//2]:.4f}s ({times[n//2]*1000:.1f}ms)')
		print(f'p95: {times[int(n*0.95)]:.4f}s ({times[int(n*0.95)]*1000:.1f}ms)')
		"
## Results	 
	Median: 0.0540s (54.0ms)
	p95: 2.0010s (2001.0ms)
	Percentile method : sorted all request time values ascending , then took the value at index int(n * 0.95) which is 95%
	Unit : seconds 

6. Which requests retried upstream? How many succeeded after retrying?

## Commands / scripts
	grep -c '"upstream":"[^"]*,[^"]*"' logs/access.log 				to count how many upstreams retried
	grep '"upstream":"[^"]*,[^"]*"' logs/access.log | grep -c '"status":200'	to count how many of those retries succeeded
## Results
	Retries count : 19
	Success count : 19 (100%)

7. Build an incident timeline using evidence from access, error AND application logs.

## Commands / scripts
	grep '"status":[45]' logs/access.log | grep -o '2026-08-20T11:[0-9][0-9]' | sort | uniq -c	to find when errors occurred
	grep '"event":"dependency_error"' logs/application.log						to see what caused those errors
	head -5 logs/error.log										to see connection refused errors
## Results
	Logs start at 11 with normal traffic , but at 11:05 there is a spike in errors
	By looking at application.log we find that this happened because app-02 became unreachable 
	Traffic returned to normal at 11:10 but at 11:12 there was another spike in errors
	By looking at application logs and error logs they show the error was a TimeOut because they couldn't reach Redis
	Traffic returned to normal at 11:15
	At 11:20 a third error spike happened
	By looking at application logs , we find that this happened because of a 'invalid password' postgreSQL error
	Traffic returned to normal at 11:22
	Another error spike happened at  11:25 
	By looking at error log files we find that this happened at the /record path with a '504 Gateway Timeout'
	This probably happened because of server slowdown or CPU spike
	Traffic returned to normal att 11:27

8. Show one correlated failed request and one successful request. Include IDs and timestamps.

## Commands / scripts
	grep '"status":502' logs/access.log | head -1					to find a failed request
	grep "lab-000122" logs/error.log , grep "lab-000122" logs/application.log	to find correlations of the same request
	grep '"status":200' logs/access.log | head -1					to find a successful request
## Results
	Failed request (ID lab-000122):
		In access.log: {"timestamp":"2026-08-20T11:05:02.503Z","request_id":"lab-000122","method":"GET","path":"/health","status":502,"upstream":"172.23.0.12:8080","upstream_status":"502","request_time":0.003,"client":"192.0.2.24"}
		In application.log: Doesn't exist because the connection was refused , so it never reached the app
		In error.log: 2026/08/20 11:05:02 [error] 31#31: *122 connect() failed (111: Connection refused) while connecting to upstream, request_id=lab-000122, request: "GET /health HTTP/1.1", upstream: "http://172.23.0.12:8080/health"
	
	Successful request(ID lab-000002):
		In access.log: {"timestamp":"2026-08-20T11:00:02.532Z","request_id":"lab-000002","method":"GET","path":"/health","status":200,"upstream":"172.23.0.12:8080","upstream_status":"200","request_time":0.032,"client":"192.0.2.24"} 
		In application.log: {"timestamp": "2026-08-20T11:00:02.532Z", "level": "INFO", "event": "http_request", "request_id": "lab-000002", "instance_id": "app-02", "method": "GET", "path": "/health", "status": 200, "duration_ms": 32.0}
		In error.log: Doesn't exist because the request went through successfully
		
9. Which errors appear to be proxy/connectivity issues versus dependency/application issues? What proves it?

## Commands / scripts
	grep -c '"status":50[24]' logs/access.log		to count 502 and 504 (proxy) errors
	grep -c "dependency_error" logs/application.log		to count dependancy (503) errors
## Results
	Proxy errors:
		There are 48 proxy errors
		Proof: 	They have code 502 or 504 which means bad gateway or gateway timeout
			They appear in error.log and access.log but not application.log , because they never reached the application
	Dependancy errors:
		There are 47 dependancy errors
		proof: application log shows 'dependancy error'
			they appear in all log files because the request was processed but it couldn't reach Redis/PostgreSQL 	

10. What do the logs not prove? What would you check next in a running environment?
	Logs don't prove: 
		Why app-02 went down
		why Redis became unavailable
		what was the losses during the outages? did we lose any data?
		Are the incidents related? or independant?
	What would I check in a running environment
		'docker events' to see container starts/stops
		'docker stats' cpu and memory usage per container
		'docker logs app-02' and 'docker inspect app-02' to figure out what happened to app-02
	
			
