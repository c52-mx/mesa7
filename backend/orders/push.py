import json
import logging
import threading
import urllib.request

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

STATUS_MESSAGES = {
    "preparing": "Tu pedido #{id} está en preparación",
    "ready": "¡Tu pedido #{id} está listo!",
    "cancelled": "Tu pedido #{id} fue cancelado",
}


def _post(messages):
    request = urllib.request.Request(
        EXPO_PUSH_URL,
        data=json.dumps(messages).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=5).read()
    except Exception:
        logger.exception("No se pudo enviar el push a Expo")


def notify_status(order, tokens):
    """Avisa al cliente del nuevo estado. La consulta de tokens la hace quien llama (hilo principal)."""
    template = STATUS_MESSAGES.get(order.status)
    if not template or not tokens:
        return
    messages = [
        {
            "to": token,
            "title": "Mesa7",
            "body": template.format(id=order.pk),
            "data": {"order_id": order.pk, "status": order.status},
            "sound": "default",
        }
        for token in tokens
    ]
    # Sin cola de tareas en el MVP: el envío va en un hilo para no frenar la petición.
    threading.Thread(target=_post, args=(messages,), daemon=True).start()
