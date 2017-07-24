#!/usr/bin/python

import os
import logging
from subprocess import call, check_output
import psutil

INDI_PORT = 7624
INDI_FIFO = '/tmp/indiFIFO'


class IndiServer(object):
    def __init__(self, fifo=INDI_FIFO):
        self.__fifo = fifo

    def __clear_fifo(self):
        logging.info("Deleting fifo %s" % self.__fifo)
        call(['rm', '-f', self.__fifo])
        call(['mkfifo', self.__fifo])

    def __run(self, port):
        cmd = 'indiserver -p %d -m 100 -v -f %s > /dev/null 2>&1 &' % \
            (port, self.__fifo)
        logging.debug(cmd)
        call(cmd, shell=True)

    def start_driver(self, driver):
        # escape quotes if they exist
        binary = driver.binary.replace('"', '\\"')

        if "@" in binary:
            cmd = 'start %s' % binary
        else:
            cmd = 'start %s -n \\"%s\\"' % (binary, driver.label)

        full_cmd = 'echo "%s" > %s' % (cmd, self.__fifo)
        logging.debug(full_cmd)
        call(full_cmd, shell=True)

    def start(self, port=INDI_PORT, drivers=[]):
        self.__clear_fifo()
        self.__run(port)

        for driver in drivers:
            self.start_driver(driver)

    def stop(self):
        cmd = ['pkill', 'indiserver']
        logging.debug(' '.join(cmd))
        call(cmd)

    def is_running(self):
        for proc in psutil.process_iter():
            if proc.name() == 'indiserver':
                return True
        return False

    def set_prop(self, dev, prop, element, value):
        cmd = ['indi_setprop', '%s.%s.%s=%s' % (dev, prop, element, value)]
        call(cmd)

    def get_prop(self, dev, prop, element):
        cmd = ['indi_getprop', '%s.%s.%s' % (dev, prop, element)]
        output = check_output(cmd)
        return output.split('=')[1].strip()

    def get_state(self, dev, prop):
        return self.get_prop(dev, prop, '_STATE')

    def get_running_drivers(self):
        drivers = [proc.name() for proc in psutil.process_iter() if
                   proc.name().startswith('indi_')]
        return drivers
