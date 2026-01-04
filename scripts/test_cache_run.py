import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.core.cache import cache
cache.set('test_cache_key','ok',30)
print('cache get:', cache.get('test_cache_key'))
