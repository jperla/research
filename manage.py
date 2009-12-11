#!/usr/bin/env python

import weby
import newword

if __name__ == '__main__':
    modules = [newword,]
    app = newword.app
    weby.tools.watcher_launcher(modules, app)

