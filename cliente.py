import grpc
import cadena_frio_pb2
import cadena_frio_pb2_grpc

ROJO = "\033[1;97;41m"   # texto blanco en negrita sobre fondo rojo
RESET = "\033[0m"


def main():
    id_camion = input("ID del camión (CAM-001 / CAM-002): ").strip()
    intervalo = int(input("Intervalo en segundos: "))

    with grpc.insecure_channel("localhost:50051") as canal:
        stub = cadena_frio_pb2_grpc.MonitorCadenaFrioStub(canal)
        peticion = cadena_frio_pb2.SuscripcionCamion(
            id_camion=id_camion, intervalo_segundos=intervalo)

        print(f"\nMonitoreando {id_camion}... (Ctrl+C para salir)\n")
        try:
            for respuesta in stub.TransmitirTelemetria(peticion):
                texto = (f"[{respuesta.timestamp}] {respuesta.id_camion} | "
                         f"{respuesta.temperatura_celsius:5.2f} °C | "
                         f"GPS ({respuesta.latitud}, {respuesta.longitud})")

                if respuesta.alerta_critica:
                    print(f"{ROJO} ALERTA CRÍTICA -> {texto} {RESET}")
                else:
                    print(f"  OK  {texto}")

        except grpc.RpcError as e:
            print(f"{ROJO} Error {e.code().name}: {e.details()} {RESET}")
        except KeyboardInterrupt:
            print("\nMonitoreo finalizado.")


if __name__ == "__main__":
    main()
