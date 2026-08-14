from django.contrib import admin
from theatre.models import (
    Actor,
    Genre,
    Play,
    TheatreHall,
    Performance,
    Reservation,
    Ticket,
)


@admin.register(Play)
class PlayAdmin(admin.ModelAdmin):
    filter_horizontal = ("actors", "genres")


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    inlines = (TicketInline,)


admin.site.register(Performance)
admin.site.register(Actor)
admin.site.register(Genre)
admin.site.register(TheatreHall)
admin.site.register(Ticket)
