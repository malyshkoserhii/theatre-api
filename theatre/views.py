from django.db.models import Count, F, QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
)
from theatre.permissions import IsAdminOrIfAuthenticatedReadOnly
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PerformanceDetailSerializer,
    PerformanceListSerializer,
    PerformanceSerializer,
    PlayDetailSerializer,
    PlayListSerializer,
    PlaySerializer,
    ReservationListSerializer,
    ReservationSerializer,
    TheatreHallSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.all()
    serializer_class = PlaySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self) -> QuerySet[Play]:
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("actors", "genres")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        if self.action == "retrieve":
            return PlayDetailSerializer

        return self.serializer_class


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = (
                queryset
                .select_related("play", "theatre_hall")
                .annotate(
                    tickets_available=(
                        F("theatre_hall__rows")
                        * F("theatre_hall__seats_in_row")
                        - Count("tickets")
                    )
                )
            )

        if self.action == "retrieve":
            queryset = (
                queryset
                .select_related("play", "theatre_hall")
                .prefetch_related("play__genres", "play__actors")
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer

        if self.action == "retrieve":
            return PerformanceDetailSerializer

        return self.serializer_class


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.prefetch_related(
            "tickets__performance__play",
            "tickets__performance__theatre_hall",
        )
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ReservationListSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
