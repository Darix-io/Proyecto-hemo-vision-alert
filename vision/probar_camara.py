import cv2
from ultralytics import YOLO

modelo = YOLO("yolov8n.pt")
camara = cv2.VideoCapture(0)
if not camara.isOpened():
    print("No se pudo abrir la cámara 0. Pruebe con 1 o con un archivo de video.")
    raise SystemExit(1)

print("Pulse la tecla q en la ventana para salir.")
while True:
    ok, cuadro = camara.read()
    if not ok:
        print("No se pudo leer un fotograma.")
        break
    resultado = modelo(cuadro, verbose=False)[0]
    cv2.imshow("HemoVision - prueba de cámara", resultado.plot())
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camara.release()
cv2.destroyAllWindows()