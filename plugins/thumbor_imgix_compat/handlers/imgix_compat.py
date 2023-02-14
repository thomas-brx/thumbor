# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.


from hashlib import md5
from math import ceil, floor
import tornado.web
from urllib.parse import urlparse, parse_qs, unquote
from os import getenv

from thumbor.handlers.imaging import ImagingHandler

class ImgxCompatHandler(ImagingHandler):

    should_return_image = True

    @classmethod
    def regex(cls):
        '''
        :return: The list of regex used for routing.
        :rtype: string
        '''
        regexp_list = getenv('IMGIX_HANDLER_REGEXP')
        return regexp_list.split(';')


    def check_imgix_signature(self, uri: str, qs: map) -> bool:
        imgix_hash = self.context.config.get('IMGIX_COMPAT_TOKEN', None)
        if imgix_hash is None:
            return False

        if 's' not in qs:
            return False

        query_signature = qs['s']

        request_uri = uri.replace(f'&s={query_signature}', '')

        check_extra_leading_slash = self.context.config.get('IMGIX_COMPAT_CHECK_LEADING_SLASH', None)

        return (
            md5((imgix_hash + request_uri).encode('utf8')).hexdigest() == query_signature[:32] or
            (check_extra_leading_slash and md5((imgix_hash + '/' + request_uri).encode('utf8')).hexdigest() == query_signature[:32])
        )


    def build_request(self):
        uri = self.request.uri
        handler_prefix = self.context.config.get('IMGIX_HANDLER_PREFIX')

        if not uri.startswith(handler_prefix):
            raise tornado.web.HTTPError(403)

        uri = uri[len(handler_prefix):]

        parsed = urlparse('/' + uri.lstrip('/'))
        qs = {k: v[-1] for k, v in parse_qs(parsed.query).items()}

        if not self.check_imgix_signature(uri, qs):
            raise tornado.web.HTTPError(403)

        filters = []
        smart = None
        halign = None
        valign = None
        height = None
        width = None
        unsafe = 'unsafe'
        fit_in = None
        adaptive = None
        full = None

        max_width = self.context.config.get('MAX_WIDTH')
        max_height = self.context.config.get('MAX_HEIGHT')

        if 'q' in qs:
            qp = int(qs['q']) / 100
            # Shift up a bit to better match the imgix quality
            q = round(20 + 80 * qp)

            filters.append('quality({})'.format(q))
        elif 'auto' in qs and qs['auto'] == 'compress':
            filters.append('quality({})'.format(self.context.config.get('IMGIX_COMPAT_AUTO_QUALITY')))

        if 'fit' in qs:
            if qs['fit'] == 'crop':
                pass
            elif qs['fit'] == 'fillmax':
                fit_in = 'fit-in'
            elif qs['fit'] == 'fill':
                fit_in = 'fit-in'
                filters.append('upscale()')
            else:
                fit_in = 'fit-in'
        
        if 'fill' in qs:
            if qs['fill'] == 'blur':
                filters.append('fill(blur)')
            elif qs['fill'] == 'solid' and 'fill-color' in qs:
                filters.append('fill({})'.format(qs['fill-color'].replace('#', '')))

        if 'h' in qs:
            height = int(qs['h'])

        if 'w' in qs:
            width = int(qs['w'])

        if 'ar' in qs:
            ar_w, ar_h = map(int, qs['ar'].split(':'))
            ratio = ar_w / ar_h

            if height is None and width is None:
                # Set to MAX_WIDTH / MAX_HEIGHT if defined
                width = max_width
                height = max_height

                if width == 0:
                    width = None
                if height == 0:
                    height = None

            if width is not None or height is not None:
                # Make sure supplied width and height are correct wrt the aspect ratio.
                # If not, adjust the dimension that is too big
                if width is None or width > height * ratio:
                    width_ceil = ceil(height * ratio)
                    width_floor = floor(height * ratio)

                    # Pick closest match
                    if width in [width_ceil, width_floor]:
                        # Keep the selected width
                        pass
                    elif abs(width_ceil / height - ratio) < abs((width_floor / height - ratio)):
                        width = width_ceil
                    elif abs(width_ceil / height - ratio) > abs((width_floor / height - ratio)):
                        width = width_floor
                    else:
                        width = round(height * ratio)

                elif height is None or height > width / ratio:
                    height_ceil = ceil(width / ratio)
                    height_floor = floor(width / ratio)

                    # Pick closest match
                    if height in [height_floor, height_ceil]:
                        pass
                    elif abs(width / height_ceil - ratio) < abs((width / height_floor - ratio)):
                        height = height_ceil
                    elif abs(width / height_ceil - ratio) > abs((width / height_floor - ratio)):
                        height = height_floor
                    else:
                        height = round(width / ratio)

            # else
            #   For the case when we have no width/height, we really need to hook into thumbor
            #   when the actual size of the image is known.
        
        if width is not None and height is not None:
            if max_width > 0 and width > max_width:
                # Scale down
                height = round(height * (max_width / width))
                width = max_width

            if max_height > 0 and height > max_height:
                # Scale down
                width = round(width * (max_height / height))
                height = max_height
        
        return {
            'unsafe': unsafe,
            'hash': None,
            'debug': None,
            'meta': None,
            'trim': None,
            'crop_left': None,
            'crop_top': None,
            'crop_right': None,
            'crop_bottom': None,
            'adaptive': adaptive,
            'full': full,
            'fit_in': fit_in,
            'horizontal_flip': None,
            'width': str(width) if width is not None else None,
            'vertical_flip': None,
            'height': str(height) if height is not None else None,
            'halign': halign,
            'valign': valign,
            'smart': smart,
            'filters': ':'.join(filters) if len(filters) > 0 else None,
            'image': self.context.config.get('IMGIX_COMPAT_STORAGE_ROOT') + unquote(parsed.path).lstrip('/'),
        }


    async def get(self, **kwargs):
        # Get the url from the shortener and parse the values.
        options = self.build_request()

        if not options:
            raise tornado.web.HTTPError(404)

        # Call the original ImageHandler.get method to serve the image.
        await super(ImgxCompatHandler, self).get(**options)
