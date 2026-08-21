from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)

GENRES_URL = reverse("theatre:genre-list")
ACTORS_URL = reverse("theatre:actor-list")
THEATRE_HALLS_URL = reverse("theatre:theatrehall-list")
PLAYS_URL = reverse("theatre:play-list")
PERFORMANCES_URL = reverse("theatre:performance-list")
RESERVATIONS_URL = reverse("theatre:reservation-list")


def sample_play(**params) -> Play:
    defaults = {
        "title": "Hamlet",
        "description": "Sample play description",
    }
    defaults.update(params)
    return Play.objects.create(**defaults)


def sample_theatre_hall(**params) -> TheatreHall:
    defaults = {
        "name": "Main Hall",
        "rows": 10,
        "seats_in_row": 12,
    }
    defaults.update(params)
    return TheatreHall.objects.create(**defaults)


def sample_performance(**params) -> Performance:
    play = params.pop("play", None) or sample_play()
    theatre_hall = params.pop("theatre_hall", None) or sample_theatre_hall()
    defaults = {
        "show_time": timezone.now(),
        "play": play,
        "theatre_hall": theatre_hall,
    }
    defaults.update(params)
    return Performance.objects.create(**defaults)


class UnauthenticatedApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_for_theatre_endpoints(self):
        endpoints = [
            GENRES_URL,
            ACTORS_URL,
            THEATRE_HALLS_URL,
            PLAYS_URL,
            PERFORMANCES_URL,
            RESERVATIONS_URL,
        ]
        for url in endpoints:
            res = self.client.get(url)
            self.assertEqual(
                res.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {url} should require authentication",
            )


class AuthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.client.force_authenticate(self.user)

    # --- Permission Tests ---
    def test_regular_user_cannot_create_play(self):
        payload = {
            "title": "New Play",
            "description": "Description",
        }
        res = self.client.post(PLAYS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_create_performance(self):
        play = sample_play()
        hall = sample_theatre_hall()
        payload = {
            "play": play.id,
            "theatre_hall": hall.id,
            "show_time": "2026-11-20T19:00:00Z",
        }
        res = self.client.post(PERFORMANCES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_create_theatre_hall(self):
        payload = {
            "name": "VIP Hall",
            "rows": 5,
            "seats_in_row": 5,
        }
        res = self.client.post(THEATRE_HALLS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- Reservation User Scoping Tests ---
    def test_user_sees_only_own_reservations(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testpassword123",
        )
        performance = sample_performance()

        # Create reservation for current user
        res_own = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            reservation=res_own,
            performance=performance,
            row=1,
            seat=1,
        )

        # Create reservation for other user
        res_other = Reservation.objects.create(user=other_user)
        Ticket.objects.create(
            reservation=res_other,
            performance=performance,
            row=2,
            seat=2,
        )

        res = self.client.get(RESERVATIONS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], res_own.id)

    # --- Ticket Validation Edge Cases ---
    def test_create_reservation_with_tickets_success(self):
        performance = sample_performance()
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id},
                {"row": 1, "seat": 2, "performance": performance.id},
            ]
        }
        res = self.client.post(RESERVATIONS_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)

    def test_cannot_book_seat_out_of_row_bounds(self):
        hall = sample_theatre_hall(rows=5, seats_in_row=5)
        performance = sample_performance(theatre_hall=hall)

        payload = {
            "tickets": [
                {
                    "row": 6,
                    "seat": 1,
                    "performance": performance.id
                }
            ]
        }
        res = self.client.post(RESERVATIONS_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_book_seat_out_of_seat_in_row_bounds(self):
        hall = sample_theatre_hall(rows=5, seats_in_row=5)
        performance = sample_performance(theatre_hall=hall)

        payload = {
            "tickets": [
                {"row": 1, "seat": 6, "performance": performance.id}
            ]
        }
        res = self.client.post(RESERVATIONS_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_book_already_taken_seat(self):
        hall = sample_theatre_hall(rows=5, seats_in_row=5)
        performance = sample_performance(theatre_hall=hall)

        existing_res = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            reservation=existing_res,
            performance=performance,
            row=1,
            seat=1,
        )

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": performance.id}
            ]
        }
        res = self.client.post(RESERVATIONS_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Filtering Tests ---
    def test_filter_plays_by_title(self):
        sample_play(title="Hamlet")
        sample_play(title="Macbeth")

        # Шукаємо за частиною слова, ігноруючи регістр (якщо в тебе icontains)
        res = self.client.get(PLAYS_URL, {"title": "ham"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Hamlet")

    def test_filter_plays_by_genres(self):
        genre1 = Genre.objects.create(name="Drama")
        genre2 = Genre.objects.create(name="Comedy")

        play1 = sample_play(title="Drama Play")
        play1.genres.add(genre1)

        play2 = sample_play(title="Comedy Play")
        play2.genres.add(genre2)

        play3 = sample_play(title="Empty Play")

        # Фільтруємо за кількома ID жанрів (наприклад: ?genres=1,2)
        res = self.client.get(PLAYS_URL, {"genres": f"{genre1.id},{genre2.id}"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)

        # Має повернути дві п'єси, ігноруючи play3
        self.assertEqual(len(results), 2)
        titles = [play["title"] for play in results]
        self.assertIn("Drama Play", titles)
        self.assertIn("Comedy Play", titles)

    # --- Annotated Fields Tests ---
    def test_performance_tickets_available_calculation(self):
        hall = sample_theatre_hall(rows=10, seats_in_row=10)
        performance = sample_performance(theatre_hall=hall)

        reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(reservation=reservation, performance=performance, row=1, seat=1)
        Ticket.objects.create(reservation=reservation, performance=performance, row=1, seat=2)

        res = self.client.get(PERFORMANCES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)

        performance_data = next(p for p in results if p["id"] == performance.id)
        self.assertEqual(performance_data["tickets_available"], 98)


class AdminUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpassword123",
        )
        self.client.force_authenticate(self.admin_user)

    def test_admin_can_create_genre(self):
        payload = {"name": "Comedy"}
        res = self.client.post(GENRES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Genre.objects.filter(name="Comedy").exists())

    def test_admin_can_create_actor(self):
        payload = {"first_name": "Leonardo", "last_name": "DiCaprio"}
        res = self.client.post(ACTORS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Actor.objects.filter(first_name="Leonardo").exists())

    def test_admin_can_create_play(self):
        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="Al", last_name="Pacino")
        payload = {
            "title": "The Godfather Play",
            "description": "Description text",
            "genres": [genre.id],
            "actors": [actor.id],
        }
        res = self.client.post(PLAYS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(title="The Godfather Play")
        self.assertIn(genre, play.genres.all())
        self.assertIn(actor, play.actors.all())

    def test_admin_can_create_theatre_hall(self):
        payload = {"name": "Red Hall", "rows": 15, "seats_in_row": 20}
        res = self.client.post(THEATRE_HALLS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TheatreHall.objects.filter(name="Red Hall").exists())
