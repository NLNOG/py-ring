#! /usr/bin/env python
"""
Exceptions defined by ringtools
"""

# ABOUT
# =====
# This file is part of:
# 
# ringtools - A generic module for running commands on nodes of the NLNOG 
# ring. More information about the ring: U{https://ring.nlnog.net}
# 
# source code: U{https://github.com/NLNOG/py-ring}
# 
# AUTHOR
# ======
# Teun Vink - teun@teun.tv

class RingException(Exception):
    """
    The generic ringtools  exception used for errors.
    """
    def __init__(self, message):
        self.message = message


    def __str__(self):
        return repr(self.message)
