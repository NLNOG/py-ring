#! /usr/bin/env python

# examples/pick.py
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
#ring.pick_nodes(5, include_hosts="bit01") 
#ring.pick_nodes(5, include_networks="amazon") 
#ring.pick_nodes(5, include_countries="fr") 
#ring.pick_nodes(5, support_ipv6_only=True) 
#ring.pick_nodes(5, support_ipv4=True)

ring.pick_nodes(5, include_countries=['fr','be'], exclude_countries=['nl'], include_networks='claranet', include_hosts='bit01')

