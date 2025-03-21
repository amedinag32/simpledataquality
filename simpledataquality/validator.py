from pandas import DataFrame, to_datetime, NaT
from re import compile
from numpy import isclose
from typing import Callable, Dict, Type
from abc import ABC, abstractmethod
from mssqldbfacade.facade import DatabaseFacade


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
    def __init__(self, id):
        self.db = DatabaseFacade()
        self.id = id

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
        query = F"""
            SELECT 
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

    def aplicar_reglas(self, df: DataFrame, reglas: DataFrame):
        """Aplica las reglas de negocio usando el patrón Strategy y Factory."""
        errores = []

        for _, regla in reglas.iterrows():
            columna, tipo, valor, mensaje = regla
            columnas = columna.split(",")

            if columnas[0] not in df.columns:
                continue
            # print("________\nregla: \n", regla)
            validador = ReglaNegocioFactory.obtener_regla(tipo)

            if validador and not validador.validar(df, columnas, valor):
                errores.append(mensaje)

        return errores