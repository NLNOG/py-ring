#! /usr/bin/env python

# examples/04-pick.py
#
# show/test some uses of the pick_nodes() 

import sys

try:
    from ringtools import ring
except ImportError:
    # ringtools probaly isn't installed yet
    sys.path.append('..')
    from ringtools import ring


# let's pick nodes
print "max 5 nodes: %s " % ring.pick_nodes(5) 
print "max 5 nodes, including bit01: %s" % ring.pick_nodes(5, inc_hosts="bit01") 
print "max 5 nodes, including one from amazon: %s" % ring.pick_nodes(5, inc_networks="amazon") 
print "max 5 nodes, including one in france: %s" % ring.pick_nodes(5, inc_countries="fr") 
print "max 5 nodes, only from atrato network: %s" % ring.pick_nodes(5, only_networks="atrato")
print "max 5 nodes, only from .nl: %s" % ring.pick_nodes(5, only_countries="nl")
print "max 5 nodes, all ipv6 only: %s " % ring.pick_nodes(5, support_ipv6_only=True) 
print "max 5 nodes, don't care about IPv6: %s " % ring.pick_nodes(5, support_ipv6_only=False) 
print "max 5 nodes, all dual stack: %s " % ring.pick_nodes(5, support_ipv4=True)
print "max 5 nodes, no IPv4 support: %s " % ring.pick_nodes(5, support_ipv4=False)

# this one should never give any results
print "max 5 nodes, ipv6 only + dual stack: %s " % ring.pick_nodes(5, support_ipv4=True, support_ipv6_only=True) 

# and we can combine these
print "max 5 nodes, ipv6 only and not in .nl: %s" % ring.pick_nodes(5, support_ipv6_only=True, ex_countries='nl')
print "max 5 nodes, at least one from claranet and one in belgium: %s" % ring.pick_nodes(5, inc_networks="claranet", inc_countries="be")
print "max 5 nodes, only from japan and poland: %s" % ring.pick_nodes(5, only_countries=["jp","pl"])
