from typing import Any

from django.conf.locale import fa
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from theatre.models import (
    Genre,
    Actor,
    TheatreHall,
    Play,
    Performance,
    Ticket,
    Reservation
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name", )
        read_only_fields = ("id", )


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")
        read_only_fields = ("id", )


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "capacity"
        )
        read_only_field = ("id", )


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = (
            "id",
            "title",
            "description",
            "actors",
            "genres",
        )
        read_only_fields = ("id", )


class PlayListSerializer(PlaySerializer):
    actors = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name"
    )
    genres = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )


class PlayDetailSerializer(PlaySerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ("id", "play", "show_time", "theatre_hall")
        read_only_fields = ("id", )


class PerformanceListSerializer(serializers.ModelSerializer):
    play_title = serializers.CharField(
        source="play.title",
        read_only=True,
    )
    theatre_hall_name = serializers.CharField(
        source="theatre_hall.name",
        read_only=True
    )
    theatre_hall_capacity = serializers.IntegerField(
        source="theatre_hall.capacity",
        read_only=True
    )
    tickets_available = serializers.IntegerField(
        read_only=True
    )

    class Meta:
        model = Performance
        fields = (
            "id",
            "play_title",
            "show_time",
            "theatre_hall_name",
            "theatre_hall_capacity",
            "tickets_available",
        )


class PerformanceDetailSerializer(
    PerformanceSerializer
):
    play = PlayDetailSerializer(many=False, read_only=True)
    theatre_hall = TheatreHallSerializer(many=False, read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs: Any) -> Any:
        data = super().validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["performance"].theatre_hall,
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "performance"
        )
        read_only_fields = ("id", )


class TicketListSerializer(TicketSerializer):
    performance = PerformanceListSerializer(
        many=False,
        read_only=True,
    )


class ReservationSerializer(
    serializers.ModelSerializer
):
    tickets = TicketSerializer(
        many=True,
        read_only=False,
        allow_empty=False,
    )

    class Meta:
        model = Reservation
        fields = (
            "id",
            "tickets",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    @transaction.atomic
    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        reservation = Reservation.objects.create(**validated_data)
        for ticket_data in tickets_data:
            Ticket.objects.create(reservation=reservation, **ticket_data)
        return reservation


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
