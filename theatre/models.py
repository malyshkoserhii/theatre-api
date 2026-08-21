from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


class Genre(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name", )

    def __str__(self) -> str:
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        ordering = ("first_name", )

    @property
    def full_name(self) -> str:
        return self.first_name + " " + self.last_name

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name


class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    actors = models.ManyToManyField(
        Actor,
        related_name="plays"
    )
    genres = models.ManyToManyField(
        Genre,
        related_name="plays"
    )

    class Meta:
        ordering = ("title", )
        verbose_name = "play"
        verbose_name_plural = "plays"

    def __str__(self) -> str:
        return self.title


class TheatreHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    class Meta:
        ordering = ("name", )

    def __str__(self) -> str:
        return self.name


class Performance(models.Model):
    class Meta:
        ordering = ("-show_time", )

    play = models.ForeignKey(
        Play,
        related_name="performances",
        on_delete=models.CASCADE
    )
    theatre_hall = models.ForeignKey(
        TheatreHall,
        related_name="performances",
        on_delete=models.CASCADE
    )
    show_time = models.DateTimeField()

    def __str__(self) -> str:
        return (
            f"{self.play.title} "
            f"({self.show_time.strftime('%Y-%m-%d %H:%M')})"
        )


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reservations",
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("created_at", )

    def __str__(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(
        Performance,
        related_name="tickets",
        on_delete=models.CASCADE
    )
    reservation = models.ForeignKey(
        Reservation,
        related_name="tickets",
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["performance", "row", "seat"],
                name="unique_performance_row_seat",
            )
        ]
        ordering = ("row", "seat")

    @staticmethod
    def validate_ticket(row, seat, theatre_hall, error_to_raise):
        for ticket_attr_value, ticket_attr_name, theatre_hall_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(theatre_hall, theatre_hall_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {theatre_hall_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        try:
            performance = self.performance
        except models.ObjectDoesNotExist:
            performance = None

        if performance and self.row is not None and self.seat is not None:
            Ticket.validate_ticket(
                self.row,
                self.seat,
                performance.theatre_hall,
                ValidationError,
            )

    def save(
        self,
        *args,
        **kwargs
    ) -> None:
        self.full_clean()
        return super(Ticket, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{str(self.performance)} "
            f"(row: {self.row}, seat: {self.seat})"
        )
