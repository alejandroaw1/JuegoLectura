"""
Genera los audios de las sílabas con voz sintética (requiere internet, una sola vez).
    pip install gTTS
    python generar_audios.py
Los archivos quedan en assets/audio/ (ma.mp3, me.mp3, ...). El juego los usa automáticamente.
Recomendación: reemplázalos después por grabaciones de una voz real (maestra o familiar),
con el mismo nombre de archivo, porque las sílabas sueltas suenan más claras así.
"""
import os
from gtts import gTTS
from juego import ETAPAS, AUDIO_DIR

os.makedirs(AUDIO_DIR, exist_ok=True)
for etapa in ETAPAS:
    for sil in etapa["silabas"]:
        destino = os.path.join(AUDIO_DIR, f"{sil.lower()}.mp3")
        if not os.path.exists(destino):
            gTTS(sil.lower(), lang="es", tld="com.mx", slow=True).save(destino)
            print("creado", destino)
