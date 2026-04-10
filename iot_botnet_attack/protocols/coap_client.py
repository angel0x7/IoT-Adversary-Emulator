# protocols/coap_client.py
import asyncio
from aiocoap import Context, Message, NON, POST

class CoAPInterface:
    def __init__(self):
        # On ne crée pas le contexte ici pour éviter les erreurs de boucle
        pass

    async def send_post_async(self, server_ip, path, payload):
        """Version asynchrone propre pour l'envoi CoAP"""
        try:
            protocol = await Context.create_client_context()
            
            # Construction du message (mtype=NON pour Non-Confirmable comme ton Arduino)
            request = Message(code=POST, payload=payload.encode('utf-8'), mtype=NON)
            request.set_request_uri(f"coap://{server_ip}/{path}")
            
            # Envoi du message
            await protocol.request(request).response
        except Exception as e:
            print(f"[!] Erreur interne CoAP : {e}")

    def send_sync(self, server_ip, path, payload):
        """Helper pour lancer la coroutine sans crash de boucle"""
        try:
            # On crée une nouvelle boucle d'événements spécifique à cet envoi
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_post_async(server_ip, path, payload))
            loop.close()
        except Exception as e:
            print(f"[!] Erreur CoAP : {e}")
