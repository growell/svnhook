#!/usr/bin/env python

from SvnHook import *

class StartCommit(SvnHook):
    """Handles start-commit hook calls."""

    def __init__(self):
        pass

    def run(self):
        raise Exception('Found the handler')
