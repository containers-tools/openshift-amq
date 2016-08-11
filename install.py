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

    def install(self):
        pass

    def install_s2i(self):
        s2i = "/usr/local/s2i"
        src = "/tmp/cct/cct-amq-openshift/s2i"

        if not os.exists(s2i):
            os.makedirs(s2i)

        for f in os.listdir(src):
            shutil.move(os.path.join(src,f), s2i)
