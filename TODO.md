## DONE:

1. Fetch the data from gossip
2. store in a database
3. Fetch data from validators
4. store updated data in a database

## TODO:

### Python:

5. For each validator fetch more data from the api?? based on pub key?
6. Check open ports for each validator -> nmap or something similar

We should have a script for each one of these and they should also update the DB.

Probably we'll split this whole thing into "modules" or "services"

The module or service should be able to run independently and should be able to update the DB.

Therefore each db interaction will be scoped to the module or service.

### Next.js:

7. API for the data ? Not really -> we could just use the next.js api routes to fetch the data

- We should have 1 api route for /validator details based on pub key
- We should have 1 api route for validator list which should be paginated and sortable?

## NOTES:

Pubkey is the primary key for the database.
