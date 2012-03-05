from root.models import Asset
from django.core.exceptions import MiddlewareNotUsed

class JevonsMiddleware():
    def __init__(self):
        try:
            root_asset = Asset.objects.get(parent__exact=None)
        except Asset.DoesNotExist:
            root_asset = Asset(name="Root", code="root", parent=None)
            root_asset.save()

        raise MiddlewareNotUsed