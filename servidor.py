import time
import random
from concurrent import futures

import grpc
import cadena_frio_pb2
import cadena_frio_pb2_grpc

# Camiones registrados en el sistema: posición inicial (lat, lon)
CAMIONES = {
    "CAM-001": (-2.1894, -79.8891),  # Guayaquil
    "CAM-002": (-0.1807, -78.4678),  # Quito
}


class MonitorCadenaFrioServicer(cadena_frio_pb2_grpc.MonitorCadenaFrioServicer):

    def TransmitirTelemetria(self, request, context):
        # Regla 1: el camión debe existir
        if request.id_camion not in CAMIONES:
            context.abort(grpc.StatusCode.NOT_FOUND,
                          f"El camión {request.id_camion} no existe")

        print(f"Cliente suscrito al camión {request.id_camion}")
        latitud, longitud = CAMIONES[request.id_camion]

        # Regla 2: generar lecturas periódicas y enviarlas con yield
        while context.is_active():
            temperatura = round(random.uniform(0.5, 10.0), 2)
            latitud += 0.01
            longitud += 0.01

            # Regla 3: alerta si sale del rango 2 °C - 8 °C
            alerta = temperatura < 2.0 or temperatura > 8.0

            print(f"  {request.id_camion}: {temperatura} °C  alerta={alerta}")

            yield cadena_frio_pb2.LecturaSensor(
                id_camion=request.id_camion,
                temperatura_celsius=temperatura,
                latitud=round(latitud, 5),
                longitud=round(longitud, 5),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                alerta_critica=alerta,
            )

            time.sleep(request.intervalo_segundos)

        print(f"Cliente desconectado del camión {request.id_camion}")


def main():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cadena_frio_pb2_grpc.add_MonitorCadenaFrioServicer_to_server(
        MonitorCadenaFrioServicer(), servidor)
    servidor.add_insecure_port("[::]:50051")
    servidor.start()
    print("Servidor escuchando en el puerto 50051...")
    servidor.wait_for_termination()


if __name__ == "__main__":
    main()
