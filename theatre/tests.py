from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Actor, Genre, Performance, Play, TheatreHall
from theatre.serializers import (
    PlayDetailSerializer,
    PlayListSerializer,
)

PLAY_URL = reverse("theatre:play-list")
PERFORMANCE_URL = reverse("theatre:performance-list")


def detail_play_url(play_id: int) -> str:
    return reverse("theatre:play-detail", args=[play_id])


def sample_genre(name: str = "Drama") -> Genre:
    return Genre.objects.create(name=name)


def sample_actor(first_name: str = "John", last_name: str = "Doe") -> Actor:
    return Actor.objects.create(first_name=first_name, last_name=last_name)


def sample_play(**params) -> Play:
    defaults = {
        "title": "Sample Play",
        "description": "Sample description",
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


class UnauthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PLAY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.client.force_authenticate(self.user)

    def test_list_plays(self):
        play = sample_play()
        genre = sample_genre()
        actor = sample_actor()

        play.genres.add(genre)
        play.actors.add(actor)

        res = self.client.get(PLAY_URL)

        plays = Play.objects.all().prefetch_related("actors", "genres")
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_plays_by_title(self):
        play1 = sample_play(title="Hamlet")
        play2 = sample_play(title="Macbeth")

        res = self.client.get(PLAY_URL, {"title": "hamlet"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_plays_by_genres(self):
        play_with_genre = sample_play(title="Drama Play")
        play_without_genre = sample_play(title="Comedy Play")

        genre1 = sample_genre(name="Drama")
        genre2 = sample_genre(name="Comedy")

        play_with_genre.genres.add(genre1)
        play_without_genre.genres.add(genre2)

        res = self.client.get(PLAY_URL, {"genres": f"{genre1.id}"})

        serializer1 = PlayListSerializer(play_with_genre)
        serializer2 = PlayListSerializer(play_without_genre)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_play_detail(self):
        play = sample_play()
        genre = sample_genre()
        actor = sample_actor()
        play.genres.add(genre)
        play.actors.add(actor)

        url = detail_play_url(play.id)
        res = self.client.get(url)

        serializer = PlayDetailSerializer(play)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_play_forbidden(self):
        payload = {
            "title": "Forbidden Play",
            "description": "Description",
        }
        res = self.client.post(PLAY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpassword123",
        )
        self.client.force_authenticate(self.admin)

    def test_create_play_with_genres_and_actors(self):
        genre = sample_genre()
        actor = sample_actor()
        payload = {
            "title": "Admin Play",
            "description": "Created by admin",
            "genres": [genre.id],
            "actors": [actor.id],
        }
        res = self.client.post(PLAY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        play = Play.objects.get(id=res.data["id"])
        genres = play.genres.all()
        actors = play.actors.all()

        self.assertEqual(genres.count(), 1)
        self.assertIn(genre, genres)
        self.assertEqual(actors.count(), 1)
        self.assertIn(actor, actors)


class PerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.client.force_authenticate(self.user)

    def test_tickets_available_calculation(self):
        hall = sample_theatre_hall(rows=10, seats_in_row=10)
        play = sample_play()
        Performance.objects.create(
            show_time="2026-10-15T19:00:00Z",
            play=play,
            theatre_hall=hall,
        )

        res = self.client.get(PERFORMANCE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["tickets_available"], 100)
