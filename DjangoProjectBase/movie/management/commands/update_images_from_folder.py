import os
import re
from django.conf import settings
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = 'Mapea imágenes locales desde media/movie/images/ a los movies en la base de datos y actualiza Movie.image.'

    def normalize_name(self, text):
        if not text:
            return ''
        text = str(text).strip().lower()
        text = re.sub(r'^m_', '', text)
        text = re.sub(r'\..*$', '', text)
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'à': 'a', 'è': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
            'ç': 'c', 'ø': 'o', 'å': 'a', 'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
            "'": '', '’': '', '"': ''
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        text = re.sub(r'[^a-z0-9]+', ' ', text)
        return text.strip()

    def handle(self, *args, **options):
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            self.stderr.write('ERROR: MEDIA_ROOT no está configurado en settings.')
            return

        images_folder = os.path.join(media_root, 'movie', 'images')
        if not os.path.isdir(images_folder):
            self.stderr.write(f'ERROR: La carpeta de imágenes no existe: {images_folder}')
            return

        files = [f for f in os.listdir(images_folder) if os.path.isfile(os.path.join(images_folder, f))]
        if not files:
            self.stderr.write(f'ERROR: no se encontraron archivos en {images_folder}')
            return

        normalized_images = {}
        for filename in files:
            base = os.path.splitext(filename)[0]
            normalized = self.normalize_name(base)
            if normalized:
                normalized_images.setdefault(normalized, []).append(filename)

        movies = Movie.objects.all()
        total = movies.count()
        self.stdout.write(f'Movies en DB: {total}, imágenes en carpeta: {len(files)}')

        updated = 0
        none_found = 0

        for movie in movies:
            title_norm = self.normalize_name(movie.title)
            candidate_files = normalized_images.get(title_norm)
            if not candidate_files:
                self.stderr.write(f'No se encontró imagen para "{movie.title}" (normalizado: "{title_norm}")')
                none_found += 1
                continue

            image_file = candidate_files[0]
            new_path = os.path.join('movie', 'images', image_file).replace('\\', '/')

            if movie.image and str(movie.image) == new_path:
                self.stdout.write(f'OK (ya actualizado): {movie.title} -> {new_path}')
                continue

            movie.image = new_path
            movie.save(update_fields=['image'])
            updated += 1
            self.stdout.write(self.style.SUCCESS(f'Actualizado: {movie.title} -> {new_path}'))

        self.stdout.write(self.style.SUCCESS(f'Resumen: total={total}, actualizados={updated}, sin_coincidir={none_found}'))
