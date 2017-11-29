import textwrap
import math

import boto3
import matplotlib
        
import io
import uuid

from flask_restful import abort, Resource, reqparse

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from env import S3_BUCKET

parser = reqparse.RequestParser()
parser.add_argument('text', required=True, help="You need to send me some text!")
parser.add_argument('bgcolor', required=False, help="Optionally, send a Hex colour for the background", default='#FFFFFF')
parser.add_argument('fgcolor', required=False, help="Optionally, send a Hex colour for the foreground (text)", default='#000000')
parser.add_argument('dpi', required=False, help="Optionally, specify the resolution of the image in DPI. (Size is around A4). If a list of values (e.g. [60, 300]) response is a list of URLs in this order.", default=60, type=int, action='append')
parser.add_argument('days_before_expire', required=False, help="Optionally, specify how many days the URL should be valid for.", default=30, type=int)


def make_poster(text, bgcolor='#FFFFFF', fgcolor='#000000', dpi=60, days=30):
    words = text.split()
    aspect_ratio = 1.414  # ISO 216
    line_spacing = 1.5
    chars_per_line = (aspect_ratio * line_spacing) * math.sqrt(len(text))
    lines = textwrap.wrap(text, chars_per_line, break_long_words=False)
    longest_line_chars = max([len(l) for l in lines])
    font_size = int(10.5 * 72. / longest_line_chars)  # Half inch padding. 72 pts/inch.
    poster_text = '\n'.join(lines)

    fig, ax= plt.subplots(1, 1, figsize=(11, 8))
    ax.axvspan(0, 1, color=bgcolor)
    ax.text(0.5, 0.5, poster_text, ha='center', va='center', fontsize=font_size, color=fgcolor, linespacing=line_spacing)
    plt.axis('off')

    poster_im = io.BytesIO()
    plt.tight_layout()
    plt.savefig(poster_im, format='png', dpi=dpi)
    poster_im.seek(0)
    s3 = boto3.client('s3')
    s3key = '{uuid}.png'.format(uuid=str(uuid.uuid4()))
    s3.upload_fileobj(poster_im, S3_BUCKET, s3key)

    posterurl = s3.generate_presigned_url('get_object', Params={
        'Bucket': S3_BUCKET, 'Key': s3key
    }, ExpiresIn=(days * 24 * 60 * 60))
    return posterurl


class PosterMaker(Resource):
    def post(self):
        args = parser.parse_args()
        text = args.get('text')
        bgcolor = args.get('bgcolor')
        fgcolor = args.get('fgcolor')
        dpi = args.get('dpi')
        days = args.get('days_before_expire')
        if len(dpi) > 1:
            return [make_poster(text, bgcolor, fgcolor, d, days) for d in dpi]
        else:
            return make_poster(text, bgcolor, fgcolor, dpi, days)
