# TODO:

- manually scan some of the ips to see if the script is working properly and what results can you get from it
- add different logging for vuln scanner
- change logging to be more like the previous one/ ask bomber about it
- delete old scripts that we don;t use and delete old cron jobs that we dont run anymore

## Front end:

- filter validator by s min - stake amount / it should be someewhere around 1000 validators / not 5000 / not 2000.
  1091 - solana leader-schedule.

- score :
- 0- 100 : open ports/ vulnerabilities. 100 is all closed - 0 is the worst from the list, everything else is a percentage of the two.

- redesign filters on history.

-
- for history, we should have the data displayed on a 1 hour basiss - most likely it's the db query we need to change
- ATM we have the version check every 5 minutes, we should change it to that.

- have a history of open ports

## NOTES:

vote key is the primary key for the database.

## DONE:

1. Fetch the data from gossip
2. store in a database
3. Fetch data from validators
4. store updated data in a database

5. For each validator fetch more data from the api?? based on pub key?
6. Check open ports for each validator -> nmap or something similar
   Probably we'll split this whole thing into "modules" or "services"
   The module or service should be able to run independently and should be able to update the DB.
   We should have a script for each one of these and they should also update the DB.
   Therefore each db interaction will be scoped to the module or service.
   create script to run ports service

Deploy.

7. API for the data ? Not really -> we could just use the next.js api routes to fetch the data

- We should have 1 api route for /validator details based on pub key
- We should have 1 api route for validator list which should be paginated and sortable?
- Mostly due to the "quick" scan type not being quite full. 0 it looks like the script is runnig so you just need to change the scan type
  Later - after initial deploys
  -vulnerability script

- Check the new cron runner script for the vulnerabilty service. you've just added it so it's not working properly 100%.
