from root.models import Asset
from django.core.exceptions import MiddlewareNotUsed
import datetime

class JevonsMiddleware():
    def __init__(self):
        try:
            root_asset = Asset.objects.get(parent__exact=None)
        except Asset.DoesNotExist:
            root_asset = Asset(parent=None, name="Root", code="root", start_date=datetime.datetime(2012, 3, 14, 13, 00))
            root_asset.save()

        raise MiddlewareNotUsed