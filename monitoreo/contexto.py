from django.conf import settings


def camara(request):
    return {
        "camara_url": settings.VISION_STREAM_URL,
        "camara_estacion": settings.VISION_STREAM_ESTACION,
    }