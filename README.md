py-ring
=======
py-ring - a python module for interacting with the NLNOG ring (being) 
written by Teun Vink.

Information on the NLNOG ring can be found at https://ring.nlnog.net. 
This module is designed to operate specifically on the NLNOG ring. 
Without access to its nodes, this code isn't that useful.

Examples
========

RING information
----------------

The module offers some information on the RING and its nodes:

    >>> from ringtools import ring
    >>> print ring.get_ring_countries()
    ['at', 'au', 'be', 'br', 'ca', 'ch', 'cl', 'cz', 'de', 'dk', 'ee', 'es', 'fi', 'fr', 'gb', 'gr', 'ie', 'is', 'it', 'jo', 'jp', 'li', 'lu', 'nc', 'nl', 'no', 'nz', 'pl', 'ps', 'pt', 'ro', 'se', 'sg', 'si', 'sk', 'tr', 'us', 'za']
    >>> print ring.get_ring_nodes(country='pl')
    ['acsystemy01', 'hosteam01', 'inotel01', 'maverick01', 'poznan01']
    >>> print ring.get_node_country('bit01')
    nl
    >>> print len(ring.get_ring_networks())       
    175

Running commands
----------------

The module offers an abstraction layer which makes it easy to interact with nodes:
    
    >>> from ringtools.node import RingNode
    >>> print RingNode('bit01').run_command('uptime').get_stdout()
    ['22:26:35 up 12 days, 15:30,  0 users,  load average: 0.49, 0.25, 0.12']
