import os
import random
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class Command(BaseCommand):
    help = "Muestra el embedding de una película seleccionada al azar"

    def handle(self, *args, **options):
        movie = Movie.objects.order_by('?').first()
        if not movie:
            self.stderr.write("No hay películas en la base de datos.")
            return

        self.stdout.write(self.style.SUCCESS(f"Película seleccionada (azar): {movie.title}"))

        if not movie.emb:
            self.stderr.write("No existe embedding almacenado para esta película.")
            return

        try:
            emb_data = np.frombuffer(movie.emb, dtype=np.float32).copy()
        except Exception as e:
            self.stderr.write(f"ERROR al decodificar el campo emb: {e}")
            return

        self.stdout.write(self.style.SUCCESS("Embedding cargado desde el campo emb de la base de datos."))
        self.stdout.write(f"Dimensión de embedding: {emb_data.size}")
        self.stdout.write("Valor seleccionado (index 0):")
        self.stdout.write(f"{emb_data[0]:.6f}")
        self.stdout.write(self.style.SUCCESS("Comando completado."))
