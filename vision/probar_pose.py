import math
import time

import cv2
from ultralytics import YOLO

modelo = YOLO("yolov8n-pose.pt")
camara = cv2.VideoCapture(0)
if not camara.isOpened():
    raise SystemExit("No se pudo abrir la cámara.")

previo = None
tiempo_previo = time.time()
print("Pulse q en la ventana para salir.")
while True:
    ok, cuadro = camara.read()
    if not ok:
        break
    r = modelo(cuadro, verbose=False)[0]
    texto = "Sin persona"
    if r.keypoints is not None and len(r.keypoints.xy) > 0:
        p = r.keypoints.xy[0].cpu().numpy()
        nariz, hi, hd = p[0], p[5], p[6]
        ci, cd = p[11], p[12]
        muni, mund = p[9], p[10]
        ancho = math.dist(hi, hd) or 1.0
        hombros = (hi + hd) / 2
        caderas = (ci + cd) / 2
        # Cabeza bajo la línea de hombros (positivo = cabeza caída)
        caida = (nariz[1] - hombros[1]) / ancho
        # Inclinación del torso respecto a la vertical, en grados
        dx, dy = hombros[0] - caderas[0], caderas[1] - hombros[1]
        inclinacion = abs(math.degrees(math.atan2(dx, dy)))
        # Velocidad de muñecas, en anchos de hombros por segundo
        ahora = time.time()
        velocidad = 0.0
        if previo is not None:
            dt = max(ahora - tiempo_previo, 1e-3)
            velocidad = (math.dist(muni, previo[0]) + math.dist(mund, previo[1])) / 2 / ancho / dt
        previo, tiempo_previo = (muni, mund), ahora
        texto = f"caida {caida:+.2f} | inclinacion {inclinacion:.0f} | velocidad {velocidad:.1f}"
        print(texto)
    cv2.putText(cuadro, texto, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    cv2.imshow("Prueba de pose", r.plot())
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
camara.release()
cv2.destroyAllWindows()
