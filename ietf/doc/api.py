# Copyright The IETF Trust 2024, All Rights Reserved
"""Doc API implementations"""
from django.db.models import OuterRef, Subquery, Prefetch, Value, JSONField
from django.db.models.functions import TruncDate
from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission
from rest_framework.viewsets import GenericViewSet

from ietf.group.models import Group
from ietf.name.models import StreamName
from ietf.utils.timezone import RPC_TZINFO
from .models import Document, DocEvent, RelatedDocument
from .serializers import RfcMetadataSerializer, RfcStatus, RfcSerializer


class RfcLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 500


class RfcFilter(filters.FilterSet):
    published = filters.DateFromToRangeFilter()
    stream = filters.ModelMultipleChoiceFilter(
        queryset=StreamName.objects.filter(used=True)
    )
    group = filters.ModelMultipleChoiceFilter(
        queryset=Group.objects.wgs(),
        field_name="group__acronym",
        to_field_name="acronym",
    )
    area = filters.ModelMultipleChoiceFilter(
        queryset=Group.objects.areas(),
        field_name="group__parent__acronym",
        to_field_name="acronym",
    )
    status = filters.MultipleChoiceFilter(
        choices=[(slug, slug) for slug in RfcStatus.status_slugs],
        method=RfcStatus.filter,
    )
    sort = filters.OrderingFilter(
        fields=(
            ("rfc_number", "number"),  # ?sort=number / ?sort=-number
            ("published", "published"),  # ?sort=published / ?sort=-published
        ),
    )


class PrefetchRelatedDocument(Prefetch):
    """Prefetch via a RelatedDocument

    Prefetches following RelatedDocument relationships to other docs. By default, includes
    those for which the current RFC is the `source`. If `reverse` is True, includes those
    for which it is the `target` instead. Defaults to only "rfc" documents.
    """

    def __init__(self, to_attr, relationship_id, reverse=False, doc_type_id="rfc"):
        super().__init__(
            lookup="targets_related" if reverse else "relateddocument_set",
            queryset=RelatedDocument.objects.filter(
                **{
                    "relationship_id": relationship_id,
                    f"{'source' if reverse else 'target'}__type_id": doc_type_id,
                }
            ),
            to_attr=to_attr,
        )


class RfcViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes: list[BasePermission] = []
    lookup_field = "rfc_number"
    queryset = (
        Document.objects.filter(type_id="rfc", rfc_number__isnull=False)
        .annotate(
            published_datetime=Subquery(
                DocEvent.objects.filter(
                    doc_id=OuterRef("pk"),
                    type="published_rfc",
                )
                .order_by("-time")
                .values("time")[:1]
            ),
        )
        .annotate(published=TruncDate("published_datetime", tzinfo=RPC_TZINFO))
        .order_by("-rfc_number")
        .prefetch_related(
            PrefetchRelatedDocument(
                to_attr="drafts",
                relationship_id="became_rfc",
                doc_type_id="draft",
                reverse=True,
            ),
            PrefetchRelatedDocument(to_attr="obsoletes", relationship_id="obs"),
            PrefetchRelatedDocument(
                to_attr="obsoleted_by", relationship_id="obs", reverse=True
            ),
            PrefetchRelatedDocument(to_attr="updates", relationship_id="updates"),
            PrefetchRelatedDocument(
                to_attr="updated_by", relationship_id="updates", reverse=True
            ),
        )
        .annotate(
            # TODO implement these fake fields for real
            is_also=Value([], output_field=JSONField()),
            see_also=Value([], output_field=JSONField()),
            formats=Value(["txt", "xml"], output_field=JSONField()),
            keywords=Value(["keyword"], output_field=JSONField()),
            errata=Value([], output_field=JSONField()),
        )
    )  # default ordering - RfcFilter may override
    pagination_class = RfcLimitOffsetPagination
    filter_backends = [filters.DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = RfcFilter
    search_fields = ["title", "abstract"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RfcSerializer
        return RfcMetadataSerializer
