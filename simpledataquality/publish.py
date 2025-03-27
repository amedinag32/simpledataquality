from requests import post
from datetime import datetime
from os import getenv



# 🎯 PATRÓN STRATEGY: Definir una interfaz común para las reglas
class Channel:
    """Clase para publicar mensajes en un canal de teams"""
    def __init__(self, webhook_url: str = getenv("TEAMS_CHANEL_WEBHOOK_URL")):
        self.webhook_url = webhook_url
    
    def publish(self, message: dict):
        # Enviar el mensaje
        response = post(self.webhook_url, json=message)
        
        # Verificar respuesta
        if response.status_code == 200:
            print("✅ Mensaje publicado correctamente en el canal de Teams 🚀")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
        

# Mensaje personalizable con TODO
# message = {
#     "type": "message",
#     "attachments": [
#         {
#             "contentType": "application/vnd.microsoft.card.adaptive",
#             "content": {
#                 "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
#                 "type": "AdaptiveCard",
#                 "version": "1.4",
#                 "body": [
#                     {
#                         "type": "TextBlock",
#                         "text": "🚀 **Reporte Diario**",
#                         "weight": "Bolder",
#                         "size": "ExtraLarge",
#                         "color": "Accent"
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": f"📅 Fecha y hora: {fecha_actual}",
#                         "wrap": True,
#                         "color": "Good"
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": "📢 **Estado del Proyecto**",
#                         "weight": "Bolder",
#                         "size": "Medium",
#                         "color": "Attention"
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": "✅ Todo está en marcha sin problemas.\n⚠️ Se detectaron pequeñas incidencias.\n❌ Atención: requiere revisión inmediata.",
#                         "wrap": True
#                     },
#                     {
#                         "type": "ColumnSet",
#                         "columns": [
#                             {
#                                 "type": "Column",
#                                 "width": "auto",
#                                 "items": [
#                                     {
#                                         "type": "Image",
#                                         "url": "https://cdn-icons-png.flaticon.com/512/847/847969.png",
#                                         "size": "Small"
#                                     }
#                                 ]
#                             },
#                             {
#                                 "type": "Column",
#                                 "width": "stretch",
#                                 "items": [
#                                     {
#                                         "type": "TextBlock",
#                                         "text": "**Responsable:** John Doe",
#                                         "wrap": True
#                                     }
#                                 ]
#                             }
#                         ]
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": "📋 **Lista de Tareas**",
#                         "weight": "Bolder",
#                         "size": "Medium"
#                     },
#                     {
#                         "type": "FactSet",
#                         "facts": [
#                             {"title": "🟢 Tarea 1:", "value": "Finalizada"},
#                             {"title": "🟡 Tarea 2:", "value": "En progreso"},
#                             {"title": "🔴 Tarea 3:", "value": "Pendiente"}
#                         ]
#                     },
#                     {
#                         "type": "TextBlock",
#                         "text": "🌎 **Ubicación del Proyecto**",
#                         "weight": "Bolder",
#                         "size": "Medium"
#                     },
#                     {
#                         "type": "Image",
#                         "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/World_map_blank_without_borders.svg/800px-World_map_blank_without_borders.svg.png",
#                         "size": "Large"
#                     }
#                 ],
#                 "actions": [
#                     {
#                         "type": "Action.OpenUrl",
#                         "title": "🔗 Ver Reporte Completo",
#                         "url": "https://www.ejemplo.com"
#                     },
#                     {
#                         "type": "Action.OpenUrl",
#                         "title": "📞 Contactar Soporte",
#                         "url": "https://www.ejemplo.com/soporte"
#                     }
#                 ]
#             }
#         }
#     ]
# }

