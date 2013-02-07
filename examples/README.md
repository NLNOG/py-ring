examples
========
The following examples are available:

01-ringinfo.py
--------------
Show some basic functionality of the ringtools module:
* get the hostnames of all node (`get_ring_nodes()`)
* get the names of the unique networks in the rings (`get_ring_networks()`)
* get a list of all countries which have ringnodes (`get_ring_countries()`)
* check if a hostname is an existing ringnode (`is_ring_node()`)
* check if a ringnode is dual stacked or IPv6 only (`node_has_ipv4()`)
* list all nodes in a specific country (`get_ring_nodes()`)
* look up in which country a node is located (`get_node_country()`)


02-single-node.py
-----------------
Show the basic features of the `RingNode` class by connecting 
to a single node, run a command, checking if the SSH connection 
(`RingNode.get_ssh_result()`) and the execution succeeded 
(`RingNode.get_exitcode()`) and printing the output 
(`RingNode.get_stdout()`) or errors (`RingNode.get_stderr()`).


03-all-nodes.py
---------------
Use the ` run_command` function to run a command (threaded) 
on all nodes of the ring, print output or errors for each 
node using the `NodeResultSet` class and it's 
`get_successful_results()` and `get_failed_results()` functions.


04-pick.py
----------
Show various variations of the `pick_nodes` function by
including, excluding and requiring hosts, countries and
networks, IPv4 support (or lack of it), and various 
combinations of these properties.


05-callback.py
--------------
Use a callback to a function in `run_command` using the `analyse` 
argument. This function can be used to perform actions after the 
(attempt to execute the) command has been completed. In this
example we use it to gather data from the output of a `ping`.
Also, some additional features of the `NodeResultSet` class
are shown: looking up specific values from all results,
sorting results based on these values 
(`NodeResultSet.get_value_sorted()`) and calculating averages 
(`NodeResultSet.get_value_avg()`).


06-resultset-grouped.py
-----------------------
Use the `NodeResultSet` class to group results by value. Show this by
doing a `dig` lookup for `www.facebook.com`, which has many
different labels around the globe and sorting them by answer.
