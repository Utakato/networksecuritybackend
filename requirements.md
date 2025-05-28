I am building a service that will monitor the solana network and provide a dashboard of the network's health.

It will only be focused on validator nodes and their security

It will keep a history of the network's health and provide a dashboard of the network's health.

For each validator we'll have history of the following:

- open ports - nmap simple scan
- open services - nmap simple scan
- vulnerabilities - nmap vuln scan
- validator version - from solana
- version changes - from solana
- time to update to latest version after release - from solana
- ip address - from solana
- identity key will be the primary key

The scope of the project is to have a dashboard that will show the health of the network and the health of the validators.

We will show a history of the validators data points.

I need to come up with a way to store the data in a way that is easy to query and visualize.
