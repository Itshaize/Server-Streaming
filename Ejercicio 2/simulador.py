"""
Simulador de sensores IoT de los camiones refrigerados.

Está separado del servidor gRPC para poder probar la lógica de negocio
(rango de temperatura y bandera de alerta) sin depender de gRPC.
"""

import math
import random
from datetime import datetime, timezone

# Rango permitido de la cadena de frío para vacunas (°C)
TEMP_MINIMA = 2.0
TEMP_MAXIMA = 8.0

# "Base de datos" de camiones registrados en el sistema.
# perfil: comportamiento simulado del equipo de refrigeración.
CAMIONES_REGISTRADOS = {
    "CAM-001": {
        "descripcion": "Ruta Guayaquil -> Quito (refrigeración estable)",
        "perfil": "estable",
        "origen": (-2.1894, -79.8891),   # Guayaquil
        "destino": (-0.1807, -78.4678),  # Quito
    },
    "CAM-002": {
        "descripcion": "Ruta Quito -> Cuenca (compresor con fallas)",
        "perfil": "inestable",
        "origen": (-0.1807, -78.4678),   # Quito
        "destino": (-2.9001, -79.0059),  # Cuenca
    },
}


def camion_existe(id_camion: str) -> bool:
    return id_camion in CAMIONES_REGISTRADOS


def es_alerta_critica(temperatura: float) -> bool:
    """Regla de negocio: alerta si baja de 2.0 °C o supera 8.0 °C."""
    return temperatura < TEMP_MINIMA or temperatura > TEMP_MAXIMA


class SimuladorCamion:
    """Genera lecturas sucesivas (temperatura + GPS) para un camión."""

    PASOS_TRAYECTO = 120  # lecturas necesarias para llegar al destino

    def __init__(self, id_camion: str, semilla: int | None = None):
        if not camion_existe(id_camion):
            raise KeyError(id_camion)
        self.id_camion = id_camion
        self.config = CAMIONES_REGISTRADOS[id_camion]
        self.rng = random.Random(semilla)
        self.paso = 0
        self.temperatura = 5.0
        self.pico_restante = 0.0  # para aperturas de puerta en CAM-001

    def _siguiente_temperatura(self) -> float:
        if self.config["perfil"] == "estable":
            # Oscila suavemente alrededor de 5 °C; ocasionalmente se abre
            # la puerta del contenedor y la temperatura sube de golpe.
            if self.pico_restante <= 0 and self.rng.random() < 0.10:
                self.pico_restante = self.rng.uniform(3.5, 4.5)
            base = 5.0 + self.rng.uniform(-0.4, 0.4)
            temp = base + self.pico_restante
            self.pico_restante *= 0.5  # el pico se disipa en las siguientes lecturas
        else:
            # Compresor defectuoso: ciclos que sobre-enfrían (< 2 °C)
            # y luego se recalientan (> 8 °C).
            temp = 5.0 + 4.3 * math.sin(self.paso * 0.45) + self.rng.uniform(-0.5, 0.5)
        return round(temp, 2)

    def _siguiente_posicion(self) -> tuple[float, float]:
        lat0, lon0 = self.config["origen"]
        lat1, lon1 = self.config["destino"]
        t = min(self.paso / self.PASOS_TRAYECTO, 1.0)
        ruido = lambda: self.rng.uniform(-0.0008, 0.0008)  # deriva del GPS
        lat = lat0 + (lat1 - lat0) * t + ruido()
        lon = lon0 + (lon1 - lon0) * t + ruido()
        return round(lat, 6), round(lon, 6)

    def siguiente_lectura(self) -> dict:
        """Devuelve un dict con los mismos campos que LecturaSensor."""
        temperatura = self._siguiente_temperatura()
        latitud, longitud = self._siguiente_posicion()
        self.paso += 1
        return {
            "id_camion": self.id_camion,
            "temperatura_celsius": temperatura,
            "latitud": latitud,
            "longitud": longitud,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "alerta_critica": es_alerta_critica(temperatura),
        }
