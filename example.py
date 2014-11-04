#!/usr/bin/env python3
import functioncheck as fc

fc.DISK_USAGE_THRESHOLD = 25

fc.printHeader("Systemreport")

hdds = fc.ungrep(fc.ungrep(fc.ungrep(fc.call('df -h'),'tmpfs'),'none'),'udev')
fc.printDf(hdds)

# Some maybe important processes
fc.printProcessStatus(["mysqld", "apache2"])

print("If you don't see errors, everything should be fine.")
