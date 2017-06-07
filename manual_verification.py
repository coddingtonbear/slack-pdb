# -*- coding: utf-8 -*-
import logging

import slackpdb

logging.basicConfig(level=logging.DEBUG)


def test():
    slackpdb.set_trace(channel=u'#что_ты_хочешь')


if __name__ == '__main__':
    test()
