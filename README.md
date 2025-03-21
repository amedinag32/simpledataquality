# Business Rules Validator

Este proyecto implementa un validador de reglas de negocio en Python utilizando `pandas` y una base de datos MSSQL.

## 📌 Características

- Validación de reglas de negocio almacenadas en la base de datos.
- Soporte para múltiples tipos de reglas como valores únicos, rangos, expresiones regulares y más.
- Capacidad para definir funciones personalizadas como validadores.
- Integración con MSSQL mediante `mssqldbfacade`.

## 📦 Instalación

Asegúrate de tener Python 3.8+ instalado y ejecuta:

```sh
pip install simpledataquality
```

## 🚀 Uso

### 1. Inicialización del validador
```python
from simpledataquality.validator import BusinessRulesValidator

validator = BusinessRulesValidator()
```

### 2. Cargar reglas de negocio desde la base de datos
```python
reglas = validator.cargar_reglas_negocio()
```

### 3. Aplicar reglas a un `DataFrame`
```python
import pandas as pd

df = pd.DataFrame({
    'edad': [20, 17],
    'salario': [45000, 60000],
    'email': ['test@example.com', 'invalid-email'],
    'codigo': ['A123', 'B456'],
    'anio': ['2025-02-15', '2025-04-10']
})

errores = validator.aplicar_reglas(df, reglas)

if errores:
    print("Errores encontrados:", errores)
else:
    print("Todos los datos son válidos.")
```

## 📖 Tipos de Reglas

Las reglas de validación se almacenan en la base de datos con los siguientes tipos:

| Tipo de Regla            | Descripción |
|--------------------------|-------------|
| **NO_NULO**             | El campo no puede ser nulo. |
| **UNICO**               | El campo debe tener valores únicos. |
| **EXPRESION_REGULAR**   | El campo debe coincidir con una expresión regular. |
| **MINIMO**              | El valor mínimo permitido. |
| **MAXIMO**              | El valor máximo permitido. |
| **CANTIDAD_REGISTROS**  | Debe haber exactamente X registros. |
| **PROMEDIO**            | El promedio del campo debe ser un valor específico. |
| **DESVIACION_ESTANDAR** | La desviación estándar debe ser un valor específico. |
| **RANGO**               | El valor debe estar dentro de un rango. |
| **RANGO_VALOR**         | Si el primer campo está en un rango, el segundo debe cumplir un valor específico. |
| **RANGO_RANGO**         | Si el primer campo está en un rango, el segundo debe estar en un subrango. |
| **FUNCION_PERSONALIZADA** | Se ejecuta una función definida por el usuario. |
| **HISTORICA_MAYOR**     | El valor debe ser mayor a un histórico de la base de datos. |
| **HISTORICA_MENOR**     | El valor debe ser menor a un histórico de la base de datos. |
| **COLUMNAS**            | Valida que ciertas columnas existan en el `DataFrame`. |

## 📂 Ejemplo de Reglas en la Base de Datos

| nombre_columna | tipo_regla | valor_regla | mensaje_error |
|---------------|-----------|-------------|----------------|
| edad | MINIMO | 18 | La edad debe ser al menos 18 años |
| salario | MAXIMO | 50000 | El salario no puede exceder los 50,000 |
| email | EXPRESION_REGULAR | `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$` | El email no es válido |
| codigo | UNICO | NULL | El código debe ser único |
| codigo | FUNCION_PERSONALIZADA | `def validar_codigo(valor): return valor.startswith("A")` | Código no válido |
| anio | RANGO | `2025-01-01,2025-03-01` | El rango de valores debe ser entre 2025-01-01 y 2025-03-01 |
| edad | RANGO | `18,45` | El rango de valores debe ser entre 18 y 45 |
| anio,salario | RANGO_VALOR | `2025-01-01,2025-02-28,40000` | En el rango de valores entre 2025-01-01 y 2025-02-28 debe tener valor de 40000 |
| salario | HISTORICA_MAYOR | `SELECT 39000 total` | El salario debe ser mayor a 39000 |

## 🔧 Extensión y Personalización

Si necesitas agregar nuevas reglas, puedes extender la clase `BusinessRulesValidator` y definir nuevas funciones de validación.

```python
class CustomValidator(BusinessRulesValidator):
    def nueva_regla(self, valor):
        return valor in ["A", "B", "C"]
```

## 🛠 Mantenimiento y Contribución

1. Clona este repositorio.
2. Instala dependencias.
3. Realiza cambios y envía un Pull Request.

---

© 2025 - Business Rules Validator
By: Alan Medina & Camila Vanegas ⚙️
