#! /usr/bin/env python

from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'./src/main/python')
sys.path.insert(0,'../s3g/')
import conveyor.client.__main__


if '__main__' == __name__:
    sys.exit(conveyor.client.__main__._main(sys.argv))
