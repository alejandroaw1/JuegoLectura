"""
Genera TODOS los audios que usa la versión 2 (vocales, consonantes, sílabas y palabras).
Requiere internet una sola vez:
    pip install gTTS
    python generar_audios.py
Los archivos quedan en assets/audio/ (a.mp3, m.mp3, ma.mp3, casa.mp3, ...).
Solo crea los que faltan, así que no pisa los audios que ya tienes ni las grabaciones propias.

Nota: para las letras sueltas la voz sintética dice el nombre de la letra ("eme").
Si prefieres el sonido ("mmm"), graba tu propia voz con el mismo nombre de archivo.
"""
import os
from gtts import gTTS
from juego_v2 import AUDIO_DIR, todos_los_audios

os.makedirs(AUDIO_DIR, exist_ok=True)
for nombre, texto in sorted(todos_los_audios().items()):
    destino = os.path.join(AUDIO_DIR, f"{nombre}.mp3")
    if os.path.exists(destino):
        continue
    gTTS(texto, lang="es", tld="com.mx", slow=len(texto) <= 3).save(destino)
    print("creado", destino)
print("Listo.")
