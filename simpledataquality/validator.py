from pandas import DataFrame, to_datetime, NaT
from re import compile
from numpy import isclose
from typing import Callable, Dict, Type
from abc import ABC, abstractmethod
from mssqldbfacade.facade import DatabaseFacade
from .publish import Channel
from datetime import datetime
import logging
import traceback

# Configuración básica
logging.basicConfig(
    level=logging.INFO,  # Nivel mínimo del log: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# 🎯 PATRÓN STRATEGY: Definir una interfaz común para las reglas
class ReglaNegocio(ABC):
    """Interfaz base para todas las reglas de negocio."""
    def __init__(self):
        self.db = DatabaseFacade()
        
    @abstractmethod
    def validar(self, df: DataFrame, columnas: list, valor: str) -> bool:
        pass

# ✅ Implementaciones específicas de reglas
class NoNuloRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return not df[columnas[0]].isnull().any()

class UnicoRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return not df[columnas[0]].duplicated().any()

class ExpresionRegularRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        regex = compile(valor)
        return df[columnas[0]].astype(str).apply(lambda x: bool(regex.match(x))).all()

class MinimoRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return df[columnas[0]].astype(float).min() >= float(valor)

class MaximoRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return df[columnas[0]].astype(float).max() <= float(valor)

class RangoRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return df[columnas[0]].apply(lambda x: BusinessRulesValidator.validar_rango(x, valor)).all()

class RangoValorRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return df.apply(lambda row: BusinessRulesValidator.validar_rango(row[columnas[0]], valor, row[columnas[1]]), axis=1).all()

class PromedioRegla(ReglaNegocio):

    def validar(self, df, columnas, valor):
        return isclose(df[columnas[0]].astype(float).mean(), float(valor), atol=0.01)
    
class FuncionRegla(ReglaNegocio):
    
    def cargar_funcion_personalizada(self, codigo: str) -> Callable:
        """Convierte código de función en una función ejecutable."""
        namespace = {}
        codigo = codigo.replace("\\", "")
        exec(codigo, namespace)
        
        # Busca la función definida en el código y la devuelve
        for key, value in namespace.items():
            if callable(value):  # Solo devuelve funciones
                return value
        
        raise ValueError("No se encontró una función válida en el código ejecutado.")

    def validar(self, df, columnas, valor):
        funcion = self.cargar_funcion_personalizada(valor)
        return df[columnas[0]].apply(funcion).all()

class DesviacionEstandarRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return isclose(df[columnas[0]].astype(float).std(), float(valor), atol=0.01)

class CantidadRegistrosRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return len(df) == int(valor)
    
class HistoricaMayorRegla(ReglaNegocio):
        
    def validar(self, df, columnas, valor):
        data = self.db.get_data(query=valor)
        total = data["total"][0]
        return df[columnas[0]].apply(lambda x: x > total).all()
    
class HistoricaMenorRegla(ReglaNegocio):
        
    def validar(self, df, columnas, valor):
        data = self.db.get_data(query=valor)
        total = data["total"][0]
        return df[columnas[0]].apply(lambda x: x < total).all()
    
class HistoricaStdRegla(ReglaNegocio):
        
    def validar(self, df, columnas, valor):
        data = self.db.get_data(query=valor)
        total = data["total"][0]
        std = data["std"][0]
        return df[columnas[0]].apply(lambda x: abs(x - total) > std).all()

class ColumnasRegla(ReglaNegocio):
    def validar(self, df, columnas, valor):
        return set(valor.split(",")) == set(df.columns)


# 🎯 PATRÓN FACTORY METHOD: Crea reglas de negocio según el tipo
class ReglaNegocioFactory:
    """Fábrica de reglas de negocio."""
    
    _reglas: Dict[str, Type[ReglaNegocio]] = {
        "NO_NULO": NoNuloRegla,
        "UNICO": UnicoRegla,
        "EXPRESION_REGULAR": ExpresionRegularRegla,
        "MINIMO": MinimoRegla,
        "MAXIMO": MaximoRegla,
        "CANTIDAD_REGISTROS": CantidadRegistrosRegla,
        "PROMEDIO": PromedioRegla,
        "DESVIACION_ESTANDAR": DesviacionEstandarRegla,
        "RANGO": RangoRegla,
        "RANGO_VALOR": RangoValorRegla,
        "RANGO_RANGO": RangoValorRegla,
        "FUNCION_PERSONALIZADA": FuncionRegla,
        "HISTORICA_MAYOR": HistoricaMayorRegla,
        "HISTORICA_MENOR": HistoricaMenorRegla,
        "COLUMNAS": ColumnasRegla,
        
    }

    @staticmethod
    def obtener_regla(tipo: str) -> ReglaNegocio:
        """Devuelve la regla de negocio correspondiente."""
        return ReglaNegocioFactory._reglas.get(tipo, None)()

# 🎯 CLASE PRINCIPAL
class BusinessRulesValidator:
    def __init__(self, id, identificador = None):
        self.db: DatabaseFacade = DatabaseFacade()
        self.id = id
        self.name = ""
        self.envio = False
        self.channel_name = None
        self.webhook = None
        self.get_name()
        self.identificador = identificador
        self.channel: Channel = Channel(self.webhook)


    def get_name(self)-> None:
        query = f"""
            SELECT 
                fd.nombre, chan.webhook, fd.envio, chan.nombre channel_name
            FROM
                dq.cat_flujo_datos fd
            INNER JOIN
                dq.cat_canal_teams chan ON chan.id = fd.cat_canal_teams_id
            WHERE
	            fd.id = {self.id}
        """
        my_name: DataFrame = self.db.get_data(query=query)
        
        if len(my_name)>0:
            self.name = my_name["nombre"][0]
            self.webhook = my_name["webhook"][0]
            self.envio = my_name["envio"][0]
            self.channel_name = my_name["channel_name"][0]
            
        

    @staticmethod
    def validar_rango(valor, rango, valor_columna=-1):
        """Valida si un valor está dentro de un rango de números o fechas."""
        limites = rango.split(",")

        if len(limites) < 2:
            raise ValueError(f"Formato de rango incorrecto: {rango}")

        try:
            inicio = to_datetime(limites[0], errors="coerce")
            if inicio is not NaT:
                fin = to_datetime(limites[1], errors="coerce")
                valor = to_datetime(valor, errors="coerce")
            else:   
                inicio = float(limites[0])
                fin = float(limites[1])
                valor = float(valor)
            
            if valor_columna != -1:
                if inicio <= valor <= fin:
                    if len(limites) == 4:
                        return float(limites[2]) <= float(valor_columna) <= float(limites[3])
                    else:
                        return float(limites[2]) == float(valor_columna)
                else:
                    return True
            
            return inicio <= valor <= fin
        except Exception:
            return False

    def cargar_reglas_negocio(self):
        """Carga las reglas de negocio desde la base de datos MSSQL."""
        query = f"""
            SELECT 
                rn.id,
                rn.nombre_columna, 
                trn.nombre AS tipo_regla, 
                rn.valor_regla, 
                rn.mensaje_error
            FROM 
                dq.tbl_reglas_negocio rn
            INNER JOIN 
                dq.cat_tipo_reglas_negocio trn ON rn.cat_tipo_reglas_negocio_id = trn.id
            WHERE
	            rn.cat_flujo_datos_id = {self.id}
        """
        return self.db.get_data(query=query)

    def fue_enviado(self, tbl_reglas_negocio_id: int, fecha_error: str, identificador: str) -> bool:
        if self.db.get_data(f"""
            SELECT 
                * 
            FROM 
                dq.his_reglas_negocio 
            WHERE 
                tbl_reglas_negocio_id = {tbl_reglas_negocio_id} 
            AND 
                fecha_error = '{fecha_error}' 
            AND 
                identificador = '{identificador}';"""
        ).empty:
            return False
        else:
            return True
    
    def guardar_error(self, tbl_reglas_negocio_id: int, fecha_error: str, detalle: str, identificador: str) -> bool:
        merge_query = f"""
            MERGE dq.his_reglas_negocio AS target
            USING(SELECT {tbl_reglas_negocio_id} tbl_reglas_negocio_id, '{fecha_error}' fecha_error, '{detalle}' detalle, '{identificador}' identificador) AS source 
            ON 
                source.tbl_reglas_negocio_id = target.tbl_reglas_negocio_id 
            AND 
                source.fecha_error = target.fecha_error
            AND 
                source.identificador = target.identificador
            WHEN MATCHED THEN
                UPDATE
                    SET
                        total_reportes = total_reportes + 1
            WHEN NOT MATCHED THEN
                INSERT(tbl_reglas_negocio_id, fecha_error, detalle, identificador)
                VALUES(source.tbl_reglas_negocio_id, source.fecha_error, source.detalle, source.identificador);
        """
        # ejecutamo merge
        self.db.transaction(merge_query)
    
    
    def aplicar_reglas(self, df: DataFrame, reglas: DataFrame):
        """Aplica las reglas de negocio usando el patrón Strategy y Factory."""
        
        fecha: str = datetime.now().strftime("%Y-%m-%d")
        errores = []

        for _, regla in reglas.iterrows():
            id, columna, tipo, valor, mensaje = regla
            columnas = columna.split(",")

            if columnas[0] not in df.columns:
                continue
            # print("________\nregla: \n", regla)
            validador = ReglaNegocioFactory.obtener_regla(tipo)

            if validador and not validador.validar(df, columnas, valor):
                errores.append(mensaje)
                self.guardar_error(int(id), fecha, mensaje, self.identificador)

        if len(errores) > 0:
            if self.envio:
                try:
                    if not self.fue_enviado(int(id), fecha, self.identificador):
                        self.channel.publish(self.build_error_message(errores))            
                    else:
                        logging.info(("Mensaje ya enviado anteriormente: " + str(id) + " - " + fecha + " - " + self.identificador))
                except Exception as e:
                    logging.error(e)
            else:
                logging.info("Tipo de mensaje sin publicacion, errores:")
                logging.error(errores)
        
        return errores
     
    def build_error_message(self, errors: list) -> dict:
        facts = []
        for error in errors:
            facts.append({"title": "📌", "value": error})
        if self.identificador != None:
            message = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.4",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "text": f"📎 **{self.name}**",
                                    "weight": "Bolder",
                                    "size": "ExtraLarge",
                                    "color": "Accent"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": f"🤖 **Identificador: {self.identificador}**",
                                    "color": "Attention"
                                },
                                
                                {
                                    "type": "TextBlock",
                                    "text": "📋 **Lista de Errores**",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "FactSet",
                                    "facts": facts,
                                    "color": "Attention"
                                },
                            ],
                        }
                    }
                ]
            }
        else:
            message = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.4",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "text": f"📎 **{self.name}**",
                                    "weight": "Bolder",
                                    "size": "ExtraLarge",
                                    "color": "Accent"
                                },
                                
                                {
                                    "type": "TextBlock",
                                    "text": "📋 **Lista de Errores**",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "FactSet",
                                    "facts": facts,
                                    "color": "Attention"
                                },
                            ],
                        }
                    }
                ]
            }
        
        
        return message   
        
        