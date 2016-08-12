"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import shutil

from cct.module import Module

# XXX: odd to put a Run inside install.py
class Run(Module):
    def run(self):
        self.logger.debug("CCT runtime script running!")
        # and now CCT will run the docker CMD, which is still the launch shell
        # script, but we can gradually move more code from that to here, and
        # then perhaps CMD should be $AMQ_HOME/bin/activemq console directly?
        # (inherited from standalone image)
        pass
