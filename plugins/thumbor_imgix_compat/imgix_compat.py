# -*- coding: utf-8 -*-

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from thumbor.utils import logger
import tornado.web

class ImgixCompat(object):

    def __init__(self, context):
        '''
        :param context: an instance of `CommunityContext`
        '''

        self.context = context
