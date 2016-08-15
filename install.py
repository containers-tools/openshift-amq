"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the MIT license. See the LICENSE file for details.
"""

import os
import shutil

from cct.module import Module

class Install(Module):

    # XXX: _check_env_vars method
    #       _ AMQ_HOME (via environment)

    def launch(self):
        src = "/tmp/cct/cct-amq-openshift/launch"
        dst = os.getenv('AMQ_HOME')
        for leaf in ['bin', 'conf']:
            s = os.path.join(src,leaf)
            for f in os.listdir(s):
                shutil.move(os.path.join(s,f), os.path.join(dst,leaf))

    def s2i(self):
        src = "/tmp/cct/cct-amq-openshift/s2i"
        dst = "/usr/local/s2i"

        if not os.path.exists(dst):
            os.makedirs(dst)

        for f in os.listdir(src):
            shutil.move(os.path.join(src,f), dst)

    def run(self):
        """
        Set up the CCT run script
        """
        self._move("/tmp/cct/cct-jboss-common/cctruntime.yaml", "/tmp")
