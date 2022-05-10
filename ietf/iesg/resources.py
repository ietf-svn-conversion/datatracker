# Copyright The IETF Trust 2014-2019, All Rights Reserved
# Autogenerated by the mkresources management command 2014-11-13 23:53


from ietf.api import ModelResource
from tastypie.constants import ALL
from tastypie.cache import SimpleCache

from ietf import api

from ietf.iesg.models import TelechatDate, Telechat, TelechatAgendaItem


class TelechatDateResource(ModelResource):
    class Meta:
        cache = SimpleCache()
        queryset = TelechatDate.objects.all()
        serializer = api.Serializer()
        #resource_name = 'telechatdate'
        ordering = ['id', ]
        filtering = { 
            "id": ALL,
            "date": ALL,
        }
api.iesg.register(TelechatDateResource())

class TelechatResource(ModelResource):
    class Meta:
        cache = SimpleCache()
        queryset = Telechat.objects.all()
        serializer = api.Serializer()
        #resource_name = 'telechat'
        ordering = ['tlechat_id', ]
        filtering = { 
            "telechat_id": ALL,
            "telechat_date": ALL,
            "minute_approved": ALL,
            "wg_news_txt": ALL,
            "iab_news_txt": ALL,
            "management_issue": ALL,
            "frozen": ALL,
            "mi_frozen": ALL,
        }
api.iesg.register(TelechatResource())

class TelechatAgendaItemResource(ModelResource):
    class Meta:
        cache = SimpleCache()
        queryset = TelechatAgendaItem.objects.all()
        serializer = api.Serializer()
        #resource_name = 'telechatagendaitem'
        ordering = ['id', ]
        filtering = { 
            "id": ALL,
            "text": ALL,
            "type": ALL,
            "title": ALL,
        }
api.iesg.register(TelechatAgendaItemResource())

