# -*- coding: utf-8 -*-
import logging

import slackpdb

logging.basicConfig(level=logging.DEBUG)


def test():
    slackpdb.set_trace(
        u'xoxb-194996974823-UGj992QUwAtJ3hwQSHnx2M6B',
        channel=u'#что_ты_хочешь'
    )


if __name__ == '__main__':
    test()
