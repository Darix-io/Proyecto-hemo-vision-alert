from django.conf import settings


def _lista():
    camaras = {settings.VISION_STREAM_ESTACION: settings.VISION_STREAM_URL}
    for par in (settings.VISION_CAMARAS or "").split(","):
        if "=" in par:
            estacion, url = par.split("=", 1)
            estacion, url = estacion.strip().upper(), url.strip()
            if estacion and url:
                camaras[estacion] = url
    return [
        {"estacion": e, "url": u, "camara": "CAM-" + e.split("-")[-1]}
        for e, u in sorted(camaras.items())
    ]


def camara(request):
    camaras = _lista()
    return {
        "camaras": camaras,
        "camaras_estaciones": [c["estacion"] for c in camaras],
        "camara_url": settings.VISION_STREAM_URL,
        "camara_estacion": settings.VISION_STREAM_ESTACION,
    }
