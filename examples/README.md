examples
========
The following examples are available:

01-ringinfo.py
--------------
Show some basic functionality of the ringtools module:
* get the hostnames of all node
* get the names of the unique networks in the rings
* get a list of all countries which have ringnodes
* check if a hostname is an existing ringnode
* check if a ringnode is dual stacked or IPv6 only
* list all nodes in a specific country
* look up in which country a node is located


02-single-node.py
-----------------
Connect to a single node, run a command, check if the
SSH connection and the execution succeeded and print
output or errors.


03-all-nodes.py
---------------
Use the `run_command` function to run a command (threaded) 
on all nodes of the ring, print output or errors for each 
node.


04-pick.py
----------
Show various variations of the `pick_nodes` function by
including, excluding and requiring hosts, countries and
networks, IPv4 support (or lack of it), and various 
combinations of these properties.


05-callback.py
--------------
Use a callback to a function using the `analyse` argument.
This function can be used to perform actions after the 
(attempt to execute the) command has been completed. In this
example we use it to gather data from the output of a `ping`.
Also, some additional features of the `NodeResultSet` class
are shown: looking up specific values from all results,
sorting results based on these values and calculating averages.
