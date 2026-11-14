"""
Videojuego Educativo de Lectoescritura 2D - Versión 2
Universidad Autónoma de Occidente - Ingeniería de software, 7° semestre

Estructura (según el documento del proyecto):
  Categoría 1 - LETRAS     : 1 Vocales | 2 Consonantes | 3 Letra inicial de una imagen
  Categoría 2 - SÍLABAS    : 4 Une las sílabas | 5 Identifica la sílaba | 6 Sílabas e imágenes
  Categoría 3 - PALABRAS   : 7 Reconoce la palabra | 8 Ordena las letras | 9 Completa la palabra

El jugador elige libremente la categoría y la actividad (no hay mundos bloqueados).
Cada actividad tiene 5 ejercicios y da de 1 a 3 estrellas. Los errores no se penalizan:
solo se repite el sonido y, tras 2 errores, aparece una pista.

Ejecutar:  python juego_v2.py
"""
import json
import math
import os
import random
import threading
import unicodedata
from array import array

import pygame

# --------------------------------------------------------------------------
# Configuración general
# --------------------------------------------------------------------------
W, H = 1280, 720
FPS = 60
BASE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE, "assets", "audio")
IMG_DIR = os.path.join(BASE, "assets", "img")
SAVE_FILE = os.path.join(BASE, "progreso_v2.json")
RONDAS_POR_NIVEL = 5

EQUIPO_L1 = "Equipo: Gloria Rebecca Luna Chin, Jorge Yamil Guerrero Valdez, Eric Alejandro Ibarra"
EQUIPO_L2 = "Cota y Sergio Gabriel Hernández Gómez. - 21 de octubre del 2026"

# Colores
BLANCO = (255, 255, 255)
NEGRO = (40, 40, 60)
BORDE = (35, 55, 120)
AMARILLO = (255, 205, 50)
VERDE = (80, 190, 80)
VERDE_OSC = (50, 150, 50)
ROJO = (230, 70, 70)
AZUL = (60, 140, 230)
MORADO = (150, 90, 215)
NARANJA = (255, 140, 40)
ROSA = (255, 130, 180)
ARCOIRIS = [(235, 70, 70), (255, 140, 40), (255, 205, 50), (80, 190, 80), (60, 140, 230), (150, 90, 215)]
COLORES_FICHA = [AZUL, NARANJA, MORADO, ROSA, VERDE]

# --------------------------------------------------------------------------
# Contenido educativo
# --------------------------------------------------------------------------
VOCALES = list("AEIOU")
CONSONANTES = list("MPLSTN")
SILABAS_BASE = [c + v for c in "MPLST" for v in VOCALES]          # MA, ME, ... TU
PALABRAS = {                                                       # palabra: sílabas (None si es de 1 sílaba o más larga)
    "ARCOÍRIS": None,
    "SOL": None,
    "PAN": None,
    "MESA": ["ME", "SA"],
    "PATO": ["PA", "TO"],
    "CASA": ["CA", "SA"],
    "LUNA": ["LU", "NA"],
    "MANO": ["MA", "NO"],
}
PALABRAS_2SIL = [p for p, s in PALABRAS.items() if s]
PALABRAS_CORTAS = [p for p in PALABRAS if p != "ARCOÍRIS"]
SILABAS_TODAS = sorted(set(SILABAS_BASE + [s for sil in PALABRAS.values() if sil for s in sil]))

CATEGORIAS = [
    {"nombre": "LETRAS", "sub": "Reconocimiento de sonidos", "niveles": [1, 2, 3], "top": AZUL, "bot": (255, 195, 40)},
    {"nombre": "SÍLABAS", "sub": "¡Une sonidos!", "niveles": [4, 5, 6], "top": (70, 180, 70), "bot": NARANJA},
    {"nombre": "PALABRAS", "sub": "¡Arma tus palabras!", "niveles": [7, 8, 9], "top": MORADO, "bot": ROJO},
]
NIVELES = {
    1: {"cat": 0, "nombre": "RECONOCE LAS VOCALES"},
    2: {"cat": 0, "nombre": "RECONOCE LAS CONSONANTES"},
    3: {"cat": 0, "nombre": "LETRA INICIAL"},
    4: {"cat": 1, "nombre": "UNE LAS SÍLABAS"},
    5: {"cat": 1, "nombre": "IDENTIFICA LA SÍLABA"},
    6: {"cat": 1, "nombre": "SÍLABAS E IMÁGENES"},
    7: {"cat": 2, "nombre": "RECONOCE LA PALABRA"},
    8: {"cat": 2, "nombre": "ORDENA LAS LETRAS"},
    9: {"cat": 2, "nombre": "COMPLETA LA PALABRA"},
}


def norm(texto):
    """Nombre de archivo sin acentos: 'ARCOÍRIS' -> 'arcoiris'."""
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def todos_los_audios():
    """{nombre_de_archivo: texto_a_decir} de todo lo que el juego puede pronunciar."""
    textos = set(VOCALES + CONSONANTES + ["C"] + SILABAS_TODAS + list(PALABRAS))
    return {norm(t): t.lower() for t in textos}


# --------------------------------------------------------------------------
# Generación de ejercicios
# --------------------------------------------------------------------------
def _opciones(correcta, pool, n=3):
    otras = [x for x in pool if x != correcta]
    ops = random.sample(otras, n - 1) + [correcta]
    random.shuffle(ops)
    return ops


def r_elegir(prompt, audio, correcta, opciones, imagen=None):
    return {"tipo": "elegir", "prompt": prompt, "audio": audio, "correcta": correcta,
            "opciones": opciones, "imagen": imagen}


def r_arrastrar(prompt, audio, slots, fichas, imagen=None):
    return {"tipo": "arrastrar", "prompt": prompt, "audio": audio, "slots": slots,
            "fichas": fichas, "imagen": imagen}


def generar_rondas(nivel):
    n = RONDAS_POR_NIVEL
    rondas = []
    if nivel == 1:
        for v in random.sample(VOCALES, n):
            rondas.append(r_elegir("¿Qué vocal escuchaste?", v, v, _opciones(v, VOCALES)))
    elif nivel == 2:
        for c in random.sample(CONSONANTES, n):
            rondas.append(r_elegir("¿Qué letra escuchaste?", c, c, _opciones(c, CONSONANTES)))
    elif nivel == 3:
        for p in random.sample(list(PALABRAS), n):
            ini = p[0]
            pool = VOCALES if ini in VOCALES else CONSONANTES + ["C"]
            rondas.append(r_elegir(f"¿Con qué letra empieza {p}?", p, ini, _opciones(ini, pool), imagen=p))
    elif nivel == 4:
        for s in random.sample(SILABAS_BASE, n):
            otra_c = random.choice([c for c in "MPLST" if c != s[0]])
            otra_v = random.choice([v for v in VOCALES if v != s[1]])
            fichas = [s[0], s[1], otra_c, otra_v]
            random.shuffle(fichas)
            rondas.append(r_arrastrar("Forma la sílaba que escuchaste", s,
                                      [{"texto": s[0]}, {"texto": s[1]}], fichas))
    elif nivel == 5:
        for s in random.sample(SILABAS_BASE, n):
            mismo_c = random.choice([x for x in SILABAS_BASE if x[0] == s[0] and x != s])
            misma_v = random.choice([x for x in SILABAS_BASE if x[1] == s[1] and x != s])
            ops = [s, mismo_c, misma_v]
            random.shuffle(ops)
            rondas.append(r_elegir("¿Qué sílaba escuchaste?", s, s, ops))
    elif nivel == 6:
        for p in random.sample(PALABRAS_2SIL, n):
            s = PALABRAS[p][0]
            rondas.append(r_elegir(f"¿Con qué sílaba empieza {p}?", p, s, _opciones(s, SILABAS_TODAS), imagen=p))
    elif nivel == 7:
        for p in random.sample(PALABRAS_CORTAS, n):
            rondas.append(r_elegir("¿Cómo se llama?", p, p, _opciones(p, PALABRAS_CORTAS), imagen=p))
    elif nivel == 8:
        for p in random.sample(PALABRAS_CORTAS, n):
            letras = list(p)
            for _ in range(10):
                random.shuffle(letras)
                if letras != list(p):
                    break
            rondas.append(r_arrastrar("Ordena las letras para formar:", p,
                                      [{"texto": c} for c in p], letras, imagen=p))
    elif nivel == 9:
        for p in random.sample(PALABRAS_2SIL, n):
            sils = PALABRAS[p]
            falta = random.randint(0, 1)
            slots = [{"texto": s, "fijo": i != falta} for i, s in enumerate(sils)]
            fichas = _opciones(sils[falta], SILABAS_TODAS)
            rondas.append(r_arrastrar("Completa la palabra:", p, slots, fichas, imagen=p))
    return rondas


# --------------------------------------------------------------------------
# Audio
# --------------------------------------------------------------------------
class Voz:
    """Reproduce assets/audio/<nombre>.(ogg|wav|mp3); si no existe usa pyttsx3 (si está instalado)."""

    def __init__(self):
        self.cache = {}
        self.pyttsx3 = None
        try:
            import pyttsx3
            self.pyttsx3 = pyttsx3
        except Exception:
            pass

    def _archivo(self, texto):
        for ext in ("ogg", "wav", "mp3"):
            ruta = os.path.join(AUDIO_DIR, f"{norm(texto)}.{ext}")
            if os.path.exists(ruta):
                return ruta
        return None

    def decir(self, texto):
        ruta = self._archivo(texto)
        if ruta:
            try:
                if ruta not in self.cache:
                    self.cache[ruta] = pygame.mixer.Sound(ruta)
                self.cache[ruta].play()
                return
            except pygame.error:
                pass
        if self.pyttsx3:
            threading.Thread(target=self._tts, args=(texto,), daemon=True).start()

    def _tts(self, texto):
        try:
            motor = self.pyttsx3.init()
            motor.setProperty("rate", 110)
            motor.say(texto.lower())
            motor.runAndWait()
        except Exception:
            pass


def crear_tono(frecuencias, dur=0.12):
    try:
        rate = 44100
        datos = array("h")
        for f in frecuencias:
            for i in range(int(rate * dur)):
                env = 1 - i / (rate * dur)
                datos.append(int(7000 * env * math.sin(2 * math.pi * f * i / rate)))
        return pygame.mixer.Sound(buffer=datos.tobytes())
    except Exception:
        return None


def reproducir(snd):
    if snd:
        snd.play()


# --------------------------------------------------------------------------
# Utilidades de dibujo
# --------------------------------------------------------------------------
def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), int(w), int(h))


def fuente(tam):
    for nombre in ("comicsansms", "arialrounded", "verdana", "arial"):
        ruta = pygame.font.match_font(nombre, bold=True)
        if ruta:
            return pygame.font.Font(ruta, tam)
    return pygame.font.Font(None, tam)


def texto_centrado(surf, texto, fnt, color, centro):
    img = fnt.render(texto, True, color)
    surf.blit(img, img.get_rect(center=centro))


def texto_borde(surf, texto, fnt, color, centro, borde=BORDE, g=2):
    img = fnt.render(texto, True, color)
    bor = fnt.render(texto, True, borde)
    r = img.get_rect(center=centro)
    for dx in range(-g, g + 1):
        for dy in range(-g, g + 1):
            if dx * dx + dy * dy <= g * g + 1:
                surf.blit(bor, (r.x + dx, r.y + dy))
    surf.blit(img, r)


def multilinea(surf, texto, fnt, color, cx, y, ancho, borde=None, g=2, interlin=4):
    lineas, act = [], ""
    for p in texto.split():
        prueba = (act + " " + p).strip()
        if fnt.size(prueba)[0] <= ancho:
            act = prueba
        else:
            lineas.append(act)
            act = p
    lineas.append(act)
    h = fnt.get_height()
    for i, l in enumerate(lineas):
        c = (cx, y + i * (h + interlin) + h // 2)
        if borde:
            texto_borde(surf, l, fnt, color, c, borde, g)
        else:
            texto_centrado(surf, l, fnt, color, c)
    return len(lineas)


_cache_titulo = {}


def titulo_arcoiris(surf, texto, fnt, centro, g=5):
    """Título con letras de colores, borde blanco y contorno oscuro (como en los bocetos)."""
    clave = (texto, id(fnt))
    if clave not in _cache_titulo:
        pad = g + 4
        ancho = sum(fnt.size(c)[0] for c in texto) + 2 * pad
        sup = pygame.Surface((ancho, fnt.get_height() + 2 * pad), pygame.SRCALPHA)
        x, ci = pad, 0
        for c in texto:
            w = fnt.size(c)[0]
            if c != " ":
                col = ARCOIRIS[ci % len(ARCOIRIS)]
                ci += 1
                oscuro, blanco, base = fnt.render(c, True, BORDE), fnt.render(c, True, BLANCO), fnt.render(c, True, col)
                for dx in range(-g, g + 1):
                    for dy in range(-g, g + 1):
                        d = dx * dx + dy * dy
                        if d <= g * g:
                            sup.blit(oscuro, (x + dx, pad + dy))
                for dx in range(-g + 2, g - 1):
                    for dy in range(-g + 2, g - 1):
                        if dx * dx + dy * dy <= (g - 2) * (g - 2):
                            sup.blit(blanco, (x + dx, pad + dy))
                sup.blit(base, (x, pad))
            x += w
        _cache_titulo[clave] = sup
    sup = _cache_titulo[clave]
    surf.blit(sup, sup.get_rect(center=centro))


def dibujar_estrella(surf, cx, cy, r, color, borde=(200, 150, 20)):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, borde, pts, max(2, int(r / 7)))


def dibujar_bocina(surf, cx, cy, r, color):
    pygame.draw.circle(surf, color, (cx, cy), r)
    pygame.draw.circle(surf, BLANCO, (cx, cy), r, 5)
    k = r / 52
    pygame.draw.polygon(surf, BLANCO, [(cx - 22 * k, cy - 10 * k), (cx - 8 * k, cy - 10 * k), (cx + 12 * k, cy - 28 * k),
                                       (cx + 12 * k, cy + 28 * k), (cx - 8 * k, cy + 10 * k), (cx - 22 * k, cy + 10 * k)])
    pygame.draw.arc(surf, BLANCO, R(cx - 4 * k, cy - 20 * k, 40 * k, 40 * k), -0.9, 0.9, max(3, int(5 * k)))
    pygame.draw.arc(surf, BLANCO, R(cx - 12 * k, cy - 32 * k, 60 * k, 64 * k), -0.9, 0.9, max(3, int(5 * k)))


def dibujar_nube(s, cx, cy, k, cara=True):
    for ox, oy, rw, rh in [(-50, -8, 100, 42), (-62, 4, 124, 36)]:
        pygame.draw.ellipse(s, BLANCO, R(cx + ox * k, cy + oy * k, rw * k, rh * k))
    pygame.draw.circle(s, BLANCO, (cx - 18 * k, cy - 14 * k), int(26 * k))
    pygame.draw.circle(s, BLANCO, (cx + 20 * k, cy - 10 * k), int(22 * k))
    if cara:
        for dx in (-12, 12):
            pygame.draw.circle(s, (80, 90, 140), (cx + dx * k, cy + 2 * k), max(2, int(3 * k)))
            pygame.draw.circle(s, (255, 170, 190), (cx + dx * 1.9 * k, cy + 10 * k), max(3, int(6 * k)))
        pygame.draw.arc(s, (80, 90, 140), R(cx - 8 * k, cy - 2 * k, 16 * k, 12 * k), math.pi, 2 * math.pi, 2)


def dibujar_nota(s, x, y, color):
    pygame.draw.ellipse(s, color, R(x, y, 16, 12))
    pygame.draw.line(s, color, (x + 15, y + 6), (x + 15, y - 26), 3)
    pygame.draw.polygon(s, color, [(x + 15, y - 26), (x + 30, y - 18), (x + 15, y - 14)])


# --------------------------------------------------------------------------
# Imágenes de objetos (dibujadas con formas; si existe assets/img/<palabra>.png se usa ese archivo)
# --------------------------------------------------------------------------
def img_sol(s, cx, cy, k):
    for i in range(12):
        a = i * math.pi / 6
        pygame.draw.line(s, NARANJA, (cx + 58 * k * math.cos(a), cy + 58 * k * math.sin(a)),
                         (cx + 84 * k * math.cos(a), cy + 84 * k * math.sin(a)), max(3, int(9 * k)))
    pygame.draw.circle(s, AMARILLO, (cx, cy), int(52 * k))
    for dx in (-18, 18):
        pygame.draw.circle(s, NEGRO, (cx + dx * k, cy - 8 * k), max(2, int(5 * k)))
    pygame.draw.arc(s, NEGRO, R(cx - 22 * k, cy - 6 * k, 44 * k, 34 * k), math.pi, 2 * math.pi, max(2, int(4 * k)))


def img_pan(s, cx, cy, k):
    pygame.draw.ellipse(s, (205, 140, 70), R(cx - 85 * k, cy - 42 * k, 170 * k, 84 * k))
    pygame.draw.ellipse(s, (150, 90, 40), R(cx - 85 * k, cy - 42 * k, 170 * k, 84 * k), max(2, int(4 * k)))
    for dx in (-40, 0, 40):
        pygame.draw.line(s, (240, 200, 130), (cx + (dx - 10) * k, cy - 20 * k), (cx + (dx + 10) * k, cy + 18 * k), max(3, int(8 * k)))


def img_pato(s, cx, cy, k):
    pygame.draw.ellipse(s, AMARILLO, R(cx - 70 * k, cy - 5 * k, 125 * k, 80 * k))
    pygame.draw.ellipse(s, (240, 170, 20), R(cx - 50 * k, cy + 15 * k, 60 * k, 35 * k))
    pygame.draw.circle(s, AMARILLO, (cx + 40 * k, cy - 35 * k), int(34 * k))
    pygame.draw.ellipse(s, NARANJA, R(cx + 58 * k, cy - 32 * k, 42 * k, 20 * k))
    pygame.draw.circle(s, NEGRO, (cx + 48 * k, cy - 45 * k), max(2, int(5 * k)))
    for dx in (-20, 15):
        pygame.draw.line(s, NARANJA, (cx + dx * k, cy + 72 * k), (cx + dx * k, cy + 90 * k), max(3, int(6 * k)))


def img_mesa(s, cx, cy, k):
    for dx in (-72, 58):
        pygame.draw.rect(s, (130, 80, 40), R(cx + dx * k, cy, 14 * k, 80 * k))
    pygame.draw.rect(s, (175, 115, 60), R(cx - 88 * k, cy - 22 * k, 176 * k, 26 * k), border_radius=8)
    pygame.draw.rect(s, (130, 80, 40), R(cx - 88 * k, cy - 22 * k, 176 * k, 26 * k), 3, border_radius=8)


def img_casa(s, cx, cy, k):
    pygame.draw.rect(s, (250, 225, 170), R(cx - 62 * k, cy - 10 * k, 124 * k, 84 * k))
    pygame.draw.polygon(s, ROJO, [(cx - 80 * k, cy - 8 * k), (cx, cy - 72 * k), (cx + 80 * k, cy - 8 * k)])
    pygame.draw.rect(s, (130, 80, 40), R(cx - 40 * k, cy + 22 * k, 32 * k, 52 * k))
    pygame.draw.rect(s, (150, 210, 250), R(cx + 14 * k, cy + 10 * k, 34 * k, 32 * k))
    pygame.draw.rect(s, BLANCO, R(cx + 14 * k, cy + 10 * k, 34 * k, 32 * k), 3)


def img_luna(s, cx, cy, k):
    pygame.draw.circle(s, AMARILLO, (cx, cy), int(62 * k))
    pygame.draw.circle(s, BLANCO, (cx + 30 * k, cy - 14 * k), int(54 * k))
    pygame.draw.circle(s, NEGRO, (cx - 28 * k, cy - 6 * k), max(2, int(4 * k)))
    dibujar_estrella(s, cx + 62 * k, cy - 52 * k, 14 * k, AMARILLO)


def img_mano(s, cx, cy, k):
    piel, borde = (255, 210, 165), (200, 150, 110)
    pygame.draw.rect(s, piel, R(cx - 42 * k, cy - 5 * k, 84 * k, 76 * k), border_radius=int(26 * k))
    for i, alto in enumerate((62, 76, 70, 56)):
        x = cx - 40 * k + i * 21 * k
        pygame.draw.rect(s, piel, R(x, cy - alto * k, 19 * k, alto * k), border_radius=int(9 * k))
        pygame.draw.rect(s, borde, R(x, cy - alto * k, 19 * k, alto * k), 2, border_radius=int(9 * k))
    pygame.draw.ellipse(s, piel, R(cx - 78 * k, cy + 5 * k, 46 * k, 20 * k))
    pygame.draw.ellipse(s, borde, R(cx - 78 * k, cy + 5 * k, 46 * k, 20 * k), 2)


def img_arcoiris(s, cx, cy, k):
    for i, c in enumerate(ARCOIRIS):
        pygame.draw.arc(s, c, R(cx - 90 * k + i * 9 * k, cy - 70 * k + i * 9 * k, (180 - i * 18) * k, (180 - i * 18) * k),
                        0, math.pi, max(4, int(11 * k)))
    dibujar_nube(s, cx - 82 * k, cy + 38 * k, 0.55 * k, cara=False)
    dibujar_nube(s, cx + 82 * k, cy + 38 * k, 0.55 * k, cara=False)


IMAGENES = {"SOL": img_sol, "PAN": img_pan, "PATO": img_pato, "MESA": img_mesa, "CASA": img_casa,
            "LUNA": img_luna, "MANO": img_mano, "ARCOÍRIS": img_arcoiris}
_cache_png = {}


def dibujar_imagen(s, palabra, cx, cy, tam):
    ruta = os.path.join(IMG_DIR, norm(palabra) + ".png")
    if os.path.exists(ruta):
        clave = (ruta, tam)
        if clave not in _cache_png:
            img = pygame.image.load(ruta).convert_alpha()
            esc = tam / max(img.get_size())
            _cache_png[clave] = pygame.transform.smoothscale(img, (int(img.get_width() * esc), int(img.get_height() * esc)))
        img = _cache_png[clave]
        s.blit(img, img.get_rect(center=(cx, cy)))
        return
    IMAGENES[palabra](s, cx, cy + 6, tam / 190)


# --------------------------------------------------------------------------
# Personajes (dibujados con formas; se pueden reemplazar por sprites PNG)
# --------------------------------------------------------------------------
def dibujar_tun(s, cx, cy, k, t, salto=0):
    cy += math.sin(t * 6) * 4 * k - salto
    pygame.draw.line(s, (110, 65, 30), (cx + 50 * k, cy + 25 * k), (cx + 100 * k, cy - 80 * k), max(2, int(15 * k)))
    pygame.draw.ellipse(s, (110, 65, 30), R(cx + 85 * k, cy - 105 * k, 32 * k, 40 * k))
    for dx in (-24, 24):
        pygame.draw.rect(s, (140, 90, 45), R(cx + (dx - 7) * k, cy + 70 * k, 14 * k, 40 * k), border_radius=6)
        pygame.draw.ellipse(s, (210, 150, 90), R(cx + (dx - 18) * k, cy + 102 * k, 36 * k, 14 * k))
    cuerpo = R(cx - 52 * k, cy - 92 * k, 104 * k, 184 * k)
    pygame.draw.rect(s, (176, 112, 56), cuerpo, border_radius=int(38 * k))
    pygame.draw.rect(s, (120, 75, 35), cuerpo, 4, border_radius=int(38 * k))
    pygame.draw.ellipse(s, (130, 80, 40), R(cx - 26 * k, cy - 84 * k, 52 * k, 20 * k), 3)
    pygame.draw.line(s, (176, 112, 56), (cx + 48 * k, cy + 5 * k), (cx + 72 * k, cy - 5 * k), max(2, int(12 * k)))
    for dx in (-22, 22):
        pygame.draw.circle(s, BLANCO, (cx + dx * k, cy - 28 * k), int(18 * k))
        pygame.draw.circle(s, NEGRO, (cx + dx * k, cy - 28 * k), int(8 * k))
    pygame.draw.ellipse(s, (90, 30, 30), R(cx - 20 * k, cy + 4 * k, 40 * k, 30 * k))
    pygame.draw.ellipse(s, (240, 120, 120), R(cx - 11 * k, cy + 18 * k, 22 * k, 14 * k))


def dibujar_tralalelo(s, cx, cy, k, t, salto=0):
    cy += math.sin(t * 5 + 1) * 4 * k - salto
    pygame.draw.polygon(s, (70, 110, 160), [(cx - 10 * k, cy - 62 * k), (cx + 30 * k, cy - 118 * k), (cx + 42 * k, cy - 55 * k)])
    for dx in (-42, 0, 42):
        pygame.draw.rect(s, (90, 140, 190), R(cx + (dx - 8) * k, cy + 55 * k, 16 * k, 45 * k))
        pygame.draw.ellipse(s, AZUL, R(cx + (dx - 22) * k, cy + 92 * k, 46 * k, 22 * k))
        pygame.draw.ellipse(s, BLANCO, R(cx + (dx - 22) * k, cy + 106 * k, 46 * k, 8 * k))
    pygame.draw.ellipse(s, (105, 150, 195), R(cx - 100 * k, cy - 70 * k, 200 * k, 140 * k))
    pygame.draw.ellipse(s, (225, 238, 248), R(cx - 70 * k, cy - 5 * k, 150 * k, 65 * k))
    pygame.draw.circle(s, BLANCO, (cx + 55 * k, cy - 25 * k), int(17 * k))
    pygame.draw.circle(s, NEGRO, (cx + 60 * k, cy - 25 * k), int(7 * k))
    pygame.draw.arc(s, NEGRO, R(cx + 20 * k, cy - 5 * k, 80 * k, 40 * k), math.pi, 2 * math.pi, 4)


def dibujar_inodorito(s, cx, cy, k, t, salto=0):
    cy += math.sin(t * 5 + 3) * 4 * k - salto
    for dx in (-26, 26):
        pygame.draw.rect(s, BLANCO, R(cx + (dx - 6) * k, cy + 62 * k, 12 * k, 30 * k))
        pygame.draw.ellipse(s, ROJO, R(cx + (dx - 18) * k, cy + 86 * k, 38 * k, 18 * k))
    pygame.draw.rect(s, (130, 215, 160), R(cx - 46 * k, cy - 100 * k, 92 * k, 92 * k), border_radius=int(22 * k))
    for i, c in enumerate(ARCOIRIS):
        pygame.draw.rect(s, c, R(cx - 46 * k + i * 15 * k, cy - 30 * k, 15 * k, 20 * k))
    pygame.draw.rect(s, BORDE, R(cx - 46 * k, cy - 100 * k, 92 * k, 92 * k), 3, border_radius=int(22 * k))
    for dx in (-16, 16):
        pygame.draw.circle(s, BLANCO, (cx + dx * k, cy - 66 * k), int(13 * k))
        pygame.draw.circle(s, NEGRO, (cx + dx * k, cy - 66 * k), int(6 * k))
    pygame.draw.arc(s, NEGRO, R(cx - 16 * k, cy - 58 * k, 32 * k, 24 * k), math.pi, 2 * math.pi, 3)
    pygame.draw.ellipse(s, (235, 240, 250), R(cx - 62 * k, cy - 14 * k, 124 * k, 84 * k))
    pygame.draw.ellipse(s, BORDE, R(cx - 62 * k, cy - 14 * k, 124 * k, 84 * k), 3)
    pygame.draw.ellipse(s, AMARILLO, R(cx - 50 * k, cy - 6 * k, 100 * k, 34 * k), max(3, int(6 * k)))


def dibujar_camarita(s, cx, cy, k, t, salto=0):
    cy += math.sin(t * 5 + 4) * 4 * k - salto
    for dx in (-22, 22):
        pygame.draw.rect(s, (110, 110, 170), R(cx + (dx - 6) * k, cy + 48 * k, 12 * k, 34 * k))
        pygame.draw.ellipse(s, ROJO, R(cx + (dx - 17) * k, cy + 76 * k, 36 * k, 16 * k))
    pygame.draw.line(s, (110, 110, 170), (cx + 56 * k, cy), (cx + 92 * k, cy - 40 * k + math.sin(t * 8) * 10 * k), max(3, int(10 * k)))
    pygame.draw.rect(s, (150, 150, 205), R(cx - 62 * k, cy - 50 * k, 124 * k, 100 * k), border_radius=int(20 * k))
    pygame.draw.rect(s, BORDE, R(cx - 62 * k, cy - 50 * k, 124 * k, 100 * k), 3, border_radius=int(20 * k))
    pygame.draw.circle(s, BLANCO, (cx, cy + 2 * k), int(36 * k))
    pygame.draw.circle(s, NEGRO, (cx + 6 * k, cy + 4 * k), int(18 * k))
    pygame.draw.circle(s, BLANCO, (cx + 12 * k, cy - 4 * k), max(2, int(6 * k)))
    pygame.draw.ellipse(s, ROJO, R(cx - 50 * k, cy - 92 * k, 100 * k, 70 * k))
    pygame.draw.ellipse(s, ROJO, R(cx - 20 * k, cy - 36 * k, 90 * k, 16 * k))
    pygame.draw.rect(s, (255, 230, 120), R(cx + 38 * k, cy - 46 * k, 16 * k, 10 * k))


PERSONAJES = [
    {"nombre": "TUN TUN SAHUR", "dib": dibujar_tun, "color": (205, 130, 50), "color2": (160, 95, 30),
     "desc": "¡El guardián del ritmo! Te acompaña a descubrir letras y sonidos."},
    {"nombre": "TRALALELO TRALALA", "dib": dibujar_tralalelo, "color": (70, 120, 225), "color2": (50, 85, 190),
     "desc": "¡El tiburón de los tenis! Te ayuda a formar divertidas sílabas."},
    {"nombre": "INODORITO ALEGRE", "dib": dibujar_inodorito, "color": (50, 175, 105), "color2": (30, 135, 80),
     "desc": "¡El más travieso! Siempre listo para celebrar cada uno de tus aciertos."},
    {"nombre": "CAMARITA CURIOSA", "dib": dibujar_camarita, "color": (225, 70, 70), "color2": (185, 45, 55),
     "desc": "¡La espía de las letras! Te guiará para encontrar las respuestas correctas."},
]


# --------------------------------------------------------------------------
# Progreso guardado
# --------------------------------------------------------------------------
def cargar_progreso():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            return {int(k): int(v) for k, v in json.load(f).get("niveles", {}).items()}
    except Exception:
        return {}


def guardar_progreso(prog):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"niveles": {str(k): v for k, v in prog.items()}}, f)
    except OSError:
        pass


def filas_rects(textos, cy, alto, gap=20):
    anchos = [110 if len(t) == 1 else 170 for t in textos]
    x = W // 2 - (sum(anchos) + gap * (len(anchos) - 1)) // 2
    rects = []
    for a in anchos:
        rects.append(pygame.Rect(x, cy - alto // 2, a, alto))
        x += a + gap
    return rects


def rects_opciones(n):
    w, h, gap = 210, 150, 25
    x = W // 2 - (n * w + (n - 1) * gap) // 2
    return [pygame.Rect(x + i * (w + gap), 470 - h // 2, w, h) for i in range(n)]


CARD = pygame.Rect(270, 135, 740, 565)


# --------------------------------------------------------------------------
# Juego
# --------------------------------------------------------------------------
class Juego:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self.pantalla = pygame.display.set_mode((W, H))
        pygame.display.set_caption("¡Lectoescritura 2D!")
        self.reloj = pygame.time.Clock()
        self.f_titulo = fuente(78)
        self.f_titulo2 = fuente(66)
        self.f_gigante = fuente(104)
        self.f_grande = fuente(76)
        self.f_palabra = fuente(60)
        self.f_btn = fuente(60)
        self.f_med = fuente(38)
        self.f_peq = fuente(26)
        self.f_xs = fuente(20)
        self.f_xxs = fuente(15)
        self.voz = Voz()
        self.sfx_ok = crear_tono([523, 659, 784], 0.12)
        self.sfx_mal = crear_tono([260, 200], 0.15)
        self.progreso = cargar_progreso()
        self.estado = "menu"
        self.cat_actual = 0
        self.nivel = 1
        self.botones = []
        self.particulas = []
        self.t = 0.0
        self.salto = 0.0
        self.mensaje, self.t_mensaje = "", 0
        self.t_auto = self.t_siguiente = None
        self.arrastrando = None
        self.resuelta = False
        self.rondas, self.ronda_i, self.errores, self.errores_total = [], 0, 0, 0
        self.estrellas_obtenidas = 0
        self._crear_fondo()

    # ---- fondo -----------------------------------------------------------
    def _crear_fondo(self):
        self.fondo = pygame.Surface((W, H))
        for y in range(0, H, 4):
            f = y / H
            c = (int(85 + 110 * f), int(195 + 40 * f), int(255 - 5 * f))
            pygame.draw.rect(self.fondo, c, (0, y, W, 4))
        for x, y, k in [(180, 150, 1.2), (470, 95, 1.0), (900, 210, 1.1), (90, 380, 0.9), (1130, 400, 1.0), (700, 60, 0.8)]:
            dibujar_nube(self.fondo, x, y, k)
        pygame.draw.ellipse(self.fondo, (120, 205, 90), R(-250, H - 210, 1000, 420))
        pygame.draw.ellipse(self.fondo, (95, 185, 75), R(450, H - 170, 1100, 380))
        pygame.draw.ellipse(self.fondo, (135, 215, 100), R(150, H - 110, 1000, 300))
        rnd = random.Random(11)
        self.decor = []
        letras = [fuente(40).render(c, True, col) for c, col in zip("BCKDAM", ARCOIRIS)]
        for i in range(26):
            tipo = rnd.choice(["nota", "estrella", "letra"])
            x, y = rnd.randint(20, W - 20), rnd.randint(25, 420)
            col = rnd.choice(ARCOIRIS)
            extra = pygame.transform.rotate(rnd.choice(letras), rnd.randint(-35, 35)) if tipo == "letra" else None
            self.decor.append((tipo, x, y, col, rnd.random() * 6, extra))

    def dibujar_fondo(self):
        s = self.pantalla
        s.blit(self.fondo, (0, 0))
        for tipo, x, y, col, fase, extra in self.decor:
            yy = y + math.sin(self.t * 1.6 + fase) * 7
            if tipo == "nota":
                dibujar_nota(s, x, yy, col)
            elif tipo == "estrella":
                dibujar_estrella(s, x, yy, 11, AMARILLO)
            else:
                s.blit(extra, extra.get_rect(center=(x, yy)))
        # sol sonriente
        sx, sy = W - 120, 100
        for i in range(14):
            a = i * math.pi / 7 + self.t * 0.4
            pygame.draw.line(s, NARANJA, (sx + 62 * math.cos(a), sy + 62 * math.sin(a)),
                             (sx + 90 * math.cos(a), sy + 90 * math.sin(a)), 9)
        pygame.draw.circle(s, AMARILLO, (sx, sy), 56)
        for dx in (-20, 20):
            pygame.draw.arc(s, NEGRO, R(sx + dx - 9, sy - 18, 18, 14), 0, math.pi, 3)
            pygame.draw.circle(s, (255, 150, 130), (sx + dx * 1.6, sy + 12), 8)
        pygame.draw.arc(s, NEGRO, R(sx - 20, sy - 6, 40, 32), math.pi, 2 * math.pi, 3)

    # ---- botones ---------------------------------------------------------
    def registrar(self, rect, accion):
        self.botones.append((rect, accion))

    def boton(self, rect, texto, color, accion, fnt=None, resaltar=False):
        r = rect.inflate(10, 10) if rect.collidepoint(pygame.mouse.get_pos()) else rect
        rad = min(36, r.h // 2)
        oscuro = tuple(max(0, c - 70) for c in color)
        claro = tuple(min(255, c + 60) for c in color)
        pygame.draw.rect(self.pantalla, oscuro, r.move(0, 7), border_radius=rad)
        pygame.draw.rect(self.pantalla, color, r, border_radius=rad)
        pygame.draw.rect(self.pantalla, claro, R(r.x + 10, r.y + 6, r.w - 20, r.h // 3), border_radius=rad // 2)
        pygame.draw.rect(self.pantalla, BLANCO, r, 5, border_radius=rad)
        if resaltar:
            pygame.draw.rect(self.pantalla, AMARILLO, r.inflate(16, 16), 7, border_radius=rad + 6)
        if texto:
            texto_borde(self.pantalla, texto, fnt or self.f_med, BLANCO, r.center, g=2)
        self.registrar(rect, accion)

    def boton_volver(self, accion):
        c = (80, 72)
        hover = pygame.Rect(0, 0, 90, 90)
        hover.center = c
        rad = 44 if hover.collidepoint(pygame.mouse.get_pos()) else 40
        pygame.draw.circle(self.pantalla, (200, 90, 10), (c[0], c[1] + 5), rad)
        pygame.draw.circle(self.pantalla, NARANJA, c, rad)
        pygame.draw.circle(self.pantalla, BLANCO, c, rad, 5)
        pygame.draw.polygon(self.pantalla, BLANCO, [(c[0] - 22, c[1] - 6), (c[0] - 2, c[1] - 24), (c[0] - 2, c[1] - 12),
                                                     (c[0] + 20, c[1] - 12), (c[0] + 20, c[1] + 4), (c[0] - 2, c[1] + 4), (c[0] - 2, c[1] + 12)])
        texto_borde(self.pantalla, "VOLVER", self.f_xxs, BLANCO, (c[0], c[1] + 18), g=1)
        self.registrar(hover, accion)

    def pie(self):
        for i, linea in enumerate((EQUIPO_L1, EQUIPO_L2)):
            w = self.f_xs.size(linea)[0]
            texto_borde(self.pantalla, linea, self.f_xs, BLANCO, (W - 20 - w // 2, H - 44 + i * 22), g=1)

    def personaje(self, idx, x, y, k, salto=0):
        PERSONAJES[idx % 4]["dib"](self.pantalla, x, y, k, self.t, salto)

    def globo(self, x, y):
        if not self.mensaje or pygame.time.get_ticks() > self.t_mensaje:
            return
        img = self.f_xs.render(self.mensaje, True, NEGRO)
        r = img.get_rect(center=(x, y)).inflate(30, 20)
        pygame.draw.rect(self.pantalla, BLANCO, r, border_radius=16)
        pygame.draw.rect(self.pantalla, NEGRO, r, 3, border_radius=16)
        pygame.draw.polygon(self.pantalla, BLANCO, [(r.centerx - 12, r.bottom - 2), (r.centerx + 12, r.bottom - 2), (r.centerx - 18, r.bottom + 20)])
        self.pantalla.blit(img, img.get_rect(center=r.center))

    def decir_mensaje(self, texto, dur=2200):
        self.mensaje, self.t_mensaje = texto, pygame.time.get_ticks() + dur

    # ---- lógica de actividades ------------------------------------------
    def estrellas_nivel(self, n):
        return self.progreso.get(n, 0)

    def iniciar_nivel(self, n):
        self.nivel = n
        self.cat_actual = NIVELES[n]["cat"]
        self.rondas = generar_rondas(n)
        self.ronda_i = 0
        self.errores_total = 0
        self.estado = "juego"
        self.nueva_ronda()

    def nueva_ronda(self):
        self.ronda = self.rondas[self.ronda_i]
        self.errores = 0
        self.resuelta = False
        self.t_siguiente = None
        self.arrastrando = None
        self.t_auto = pygame.time.get_ticks() + 700
        r = self.ronda
        if r["tipo"] == "elegir":
            self.rects_op = rects_opciones(len(r["opciones"]))
            self.decir_mensaje("¡Escucha!")
        else:
            textos = [s["texto"] for s in r["slots"]]
            self.slots = []
            for s, rect in zip(r["slots"], filas_rects(textos, 470, 120)):
                fijo = s.get("fijo", False)
                self.slots.append({"rect": rect, "texto": s["texto"], "fijo": fijo, "lleno": fijo})
            self.fichas = []
            for texto, rect in zip(r["fichas"], filas_rects(r["fichas"], 610, 110)):
                self.fichas.append({"texto": texto, "rect": rect, "casa": rect.copy(), "colocada": False})
            self.decir_mensaje("¡Arrastra!")

    def acierto(self):
        if self.resuelta:
            return
        self.resuelta = True
        self.salto = 40
        reproducir(self.sfx_ok)
        self.decir_mensaje("¡Muy bien!", 1600)
        self.confeti(W // 2, 280)
        self.t_auto = pygame.time.get_ticks() + 350 if self.ronda["tipo"] == "arrastrar" else None
        self.t_siguiente = pygame.time.get_ticks() + 1800

    def fallo(self):
        self.errores += 1
        self.errores_total += 1
        reproducir(self.sfx_mal)
        self.decir_mensaje("¡Otra vez!" if self.errores < 2 else "¡Tú puedes!", 1500)
        self.t_auto = pygame.time.get_ticks() + 500   # repite el sonido como pista

    def avanzar(self):
        self.ronda_i += 1
        if self.ronda_i >= len(self.rondas):
            e = self.errores_total
            self.estrellas_obtenidas = 3 if e <= 1 else 2 if e <= 4 else 1
            self.progreso[self.nivel] = max(self.estrellas_nivel(self.nivel), self.estrellas_obtenidas)
            guardar_progreso(self.progreso)
            self.estado = "resultados"
            reproducir(self.sfx_ok)
            self.salto = 40
            for _ in range(5):
                self.confeti(random.randint(250, 1000), 220)
        else:
            self.nueva_ronda()

    def confeti(self, x, y):
        for _ in range(35):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(2, 8)
            self.particulas.append([x, y, math.cos(a) * v, math.sin(a) * v - 3, random.choice(ARCOIRIS), 70])

    def elegir(self, op):
        if self.resuelta:
            return
        if op == self.ronda["correcta"]:
            self.acierto()
        else:
            self.fallo()

    def soltar_ficha(self, ficha):
        centro = ficha["rect"].center
        for slot in self.slots:
            if slot["rect"].collidepoint(centro) and not slot["lleno"]:
                if slot["texto"] == ficha["texto"]:
                    ficha["rect"].center = slot["rect"].center
                    ficha["colocada"] = True
                    slot["lleno"] = True
                    reproducir(self.sfx_ok)
                    if all(s["lleno"] for s in self.slots):
                        self.acierto()
                    return
                ficha["rect"] = ficha["casa"].copy()
                self.fallo()
                return
        ficha["rect"] = ficha["casa"].copy()

    # ---- entrada ---------------------------------------------------------
    def evento(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, accion in reversed(self.botones):
                if rect.collidepoint(e.pos):
                    accion()
                    return
            if self.estado == "juego" and self.ronda["tipo"] == "arrastrar" and not self.resuelta:
                for f in reversed(self.fichas):
                    if not f["colocada"] and f["rect"].collidepoint(e.pos):
                        self.arrastrando = f
                        f["dx"], f["dy"] = f["rect"].x - e.pos[0], f["rect"].y - e.pos[1]
                        break
        elif e.type == pygame.MOUSEMOTION and self.arrastrando:
            self.arrastrando["rect"].x = e.pos[0] + self.arrastrando["dx"]
            self.arrastrando["rect"].y = e.pos[1] + self.arrastrando["dy"]
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.arrastrando:
            f, self.arrastrando = self.arrastrando, None
            self.soltar_ficha(f)

    def actualizar(self, dt):
        self.t += dt
        ahora = pygame.time.get_ticks()
        if self.salto > 0:
            self.salto = max(0, self.salto - 80 * dt)
        if self.estado == "juego":
            if self.t_auto and ahora >= self.t_auto:
                self.t_auto = None
                self.voz.decir(self.ronda["audio"])
            if self.t_siguiente and ahora >= self.t_siguiente:
                self.t_siguiente = None
                self.avanzar()
        for p in self.particulas:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.25
            p[5] -= 1
        self.particulas = [p for p in self.particulas if p[5] > 0]

    # ---- pantallas -------------------------------------------------------
    def dibujar(self):
        self.botones = []
        self.dibujar_fondo()
        getattr(self, f"pantalla_{self.estado}")()
        for x, y, _, _, c, _ in self.particulas:
            pygame.draw.rect(self.pantalla, c, (x, y, 10, 10))
        pygame.display.flip()

    def ir(self, estado):
        self.estado = estado

    def pantalla_menu(self):
        titulo_arcoiris(self.pantalla, "¡LECTOESCRITURA 2D!", self.f_titulo, (W // 2, 120))
        self.personaje(0, 380, 470, 1.3)
        self.personaje(1, 985, 490, 1.1)
        self.boton(R(555, 330, 290, 120), "¡JUGAR!", VERDE, lambda: self.ir("categorias"), self.f_btn)
        self.boton(R(555, 480, 290, 80), "Personajes", NARANJA, lambda: self.ir("personajes"), self.f_med)
        texto_borde(self.pantalla, "Niños de 4 a 6 años", self.f_peq, BLANCO, (700, 600), g=2)
        texto_borde(self.pantalla, "Con la participación de", self.f_peq, BLANCO, (190, 588), g=2)
        texto_borde(self.pantalla, "Tun Tun Sahur y Tralalelo Tralala", self.f_peq, AMARILLO, (260, 624), g=2)
        self.pie()

    def mini_arte(self, i, rect):
        s = self.pantalla
        if i == 0:
            for j, (c, col) in enumerate(zip("ABCD", (ROJO, NARANJA, VERDE, AZUL))):
                r = R(rect.x + 16 + (j % 2) * 108, rect.y + 28 + (j // 2) * 92, 80, 76)
                pygame.draw.rect(s, col, r, border_radius=16)
                pygame.draw.rect(s, BLANCO, r, 4, border_radius=16)
                texto_centrado(s, c, self.f_grande if False else self.f_med, BLANCO, r.center)
        elif i == 1:
            for j, (a, b) in enumerate((("MA", "PA"), ("PE", "TO"))):
                y = rect.y + 34 + j * 88
                for x, t, col in ((rect.x + 14, a, ROJO), (rect.x + 130, b, AZUL)):
                    r = R(x, y, 90, 66)
                    pygame.draw.rect(s, col, r, border_radius=14)
                    pygame.draw.rect(s, BLANCO, r, 4, border_radius=14)
                    texto_centrado(s, t, self.f_med, BLANCO, r.center)
                pygame.draw.polygon(s, BLANCO, [(rect.x + 108, y + 24), (rect.x + 124, y + 33), (rect.x + 108, y + 42)])
        else:
            for j, (p, col) in enumerate((("SOL", AMARILLO), ("PAN", BLANCO), ("PATO", AMARILLO))):
                texto_borde(s, p, self.f_med, col, (rect.centerx, rect.y + 44 + j * 58), g=2)

    def pantalla_categorias(self):
        self.boton_volver(lambda: self.ir("menu"))
        titulo_arcoiris(self.pantalla, "¡ELIGE UNA CATEGORÍA!", self.f_titulo2, (W // 2, 120), g=4)
        self.personaje(0, 110, 530, 0.95)
        self.personaje(1, 1175, 540, 0.85)
        for i, cat in enumerate(CATEGORIAS):
            r = R(230 + i * 280, 200, 260, 400)
            hover = r.collidepoint(pygame.mouse.get_pos())
            rr = r.inflate(12, 12) if hover else r
            pygame.draw.rect(self.pantalla, BLANCO, rr.inflate(14, 14), border_radius=30)
            top = R(rr.x, rr.y, rr.w, rr.h * 0.58)
            pygame.draw.rect(self.pantalla, cat["top"], rr, border_radius=26)
            pygame.draw.rect(self.pantalla, cat["bot"], R(rr.x, rr.y + rr.h * 0.58, rr.w, rr.h * 0.42), border_bottom_left_radius=26,
                             border_bottom_right_radius=26)
            self.mini_arte(i, top)
            texto_borde(self.pantalla, cat["nombre"], self.f_med, BLANCO, (rr.centerx, rr.y + rr.h * 0.58 + 50), g=3)
            multilinea(self.pantalla, cat["sub"], self.f_xs, BLANCO, rr.centerx, rr.y + rr.h * 0.58 + 84, rr.w - 24, borde=BORDE, g=1)
            self.registrar(r, lambda i=i: (setattr(self, "cat_actual", i), self.ir("niveles")))
        self.pie()

    def pantalla_niveles(self):
        cat = CATEGORIAS[self.cat_actual]
        self.boton_volver(lambda: self.ir("categorias"))
        titulo_arcoiris(self.pantalla, f"¡{cat['nombre']}!", self.f_titulo, (W // 2, 120))
        self.personaje(self.cat_actual, 110, 530, 0.95)
        self.personaje(self.cat_actual + 1, 1175, 540, 0.85)
        for i, n in enumerate(cat["niveles"]):
            r = R(230 + i * 280, 215, 260, 370)
            hover = r.collidepoint(pygame.mouse.get_pos())
            rr = r.inflate(12, 12) if hover else r
            pygame.draw.rect(self.pantalla, BLANCO, rr.inflate(14, 14), border_radius=30)
            pygame.draw.rect(self.pantalla, (255, 250, 235), rr, border_radius=26)
            pygame.draw.rect(self.pantalla, cat["top"], R(rr.x, rr.y, rr.w, 70), border_top_left_radius=26, border_top_right_radius=26)
            texto_borde(self.pantalla, f"Actividad {n}", self.f_med, BLANCO, (rr.centerx, rr.y + 36), g=2)
            pygame.draw.circle(self.pantalla, cat["bot"], (rr.centerx, rr.y + 150), 55)
            pygame.draw.circle(self.pantalla, BLANCO, (rr.centerx, rr.y + 150), 55, 5)
            texto_borde(self.pantalla, str(n), self.f_gigante, BLANCO, (rr.centerx, rr.y + 150), g=3)
            multilinea(self.pantalla, NIVELES[n]["nombre"], self.f_peq, cat["top"], rr.centerx, rr.y + 225, rr.w - 30, borde=None)
            ganadas = self.estrellas_nivel(n)
            for j in range(3):
                dibujar_estrella(self.pantalla, rr.centerx - 50 + j * 50, rr.bottom - 38, 20,
                                 AMARILLO if j < ganadas else (215, 215, 215), (200, 150, 20) if j < ganadas else (170, 170, 170))
            self.registrar(r, lambda n=n: self.iniciar_nivel(n))
        self.pie()

    def pantalla_personajes(self):
        self.boton_volver(lambda: self.ir("menu"))
        titulo_arcoiris(self.pantalla, "¡NUESTROS PERSONAJES!", self.f_titulo2, (W // 2, 120), g=4)
        for i, p in enumerate(PERSONAJES):
            r = R(70 + i * 290, 200, 270, 440)
            pygame.draw.rect(self.pantalla, BLANCO, r.inflate(14, 14), border_radius=30)
            pygame.draw.rect(self.pantalla, p["color"], r, border_radius=26)
            pygame.draw.rect(self.pantalla, p["color2"], R(r.x, r.y + 270, r.w, 170), border_bottom_left_radius=26, border_bottom_right_radius=26)
            multilinea(self.pantalla, p["nombre"], self.f_peq, BLANCO, r.centerx, r.y + 14, r.w - 24, borde=BORDE, g=2)
            p["dib"](self.pantalla, r.centerx, r.y + 185, 0.9, self.t + i, 0)
            multilinea(self.pantalla, p["desc"], self.f_xs, BLANCO, r.centerx, r.y + 290, r.w - 28, borde=BORDE, g=1)
        self.pie()

    # ---- actividad -------------------------------------------------------
    def pantalla_juego(self):
        cat = CATEGORIAS[NIVELES[self.nivel]["cat"]]
        self.boton_volver(lambda: self.ir("niveles"))
        etiqueta = f"{self.nivel}. {NIVELES[self.nivel]['nombre']}"
        w = self.f_med.size(etiqueta)[0] + 70
        banner = pygame.Rect(0, 0, w, 56)
        banner.center = (W // 2, 48)
        pygame.draw.rect(self.pantalla, cat["top"], banner, border_radius=28)
        pygame.draw.rect(self.pantalla, BLANCO, banner, 5, border_radius=28)
        texto_borde(self.pantalla, etiqueta, self.f_med, BLANCO, banner.center, g=2)
        n = len(self.rondas)
        for i in range(n):
            hecha = i < self.ronda_i or (i == self.ronda_i and self.resuelta)
            dibujar_estrella(self.pantalla, W // 2 - (n - 1) * 22 + i * 44, 105, 17,
                             AMARILLO if hecha else (225, 225, 225), (200, 150, 20) if hecha else (175, 175, 175))
        pygame.draw.rect(self.pantalla, BLANCO, CARD, border_radius=34)
        pygame.draw.rect(self.pantalla, cat["top"], CARD, 8, border_radius=34)
        idx = (self.nivel - 1) % 4
        self.personaje(idx, 125, 500, 0.9, self.salto)
        self.personaje(idx + 1, 1160, 500, 0.8)
        self.globo(135, 330)

        r = self.ronda
        texto_centrado(self.pantalla, r["prompt"], self.f_med, NEGRO, (W // 2, 188))
        # imagen o bocina
        if r["imagen"]:
            marco = R(W // 2 - 90, 215, 180, 170)
            pygame.draw.rect(self.pantalla, (245, 250, 255), marco, border_radius=24)
            pygame.draw.rect(self.pantalla, cat["bot"], marco, 5, border_radius=24)
            dibujar_imagen(self.pantalla, r["imagen"], marco.centerx, marco.centery, 150)
            bx, by, br = W // 2 + 170, 300, 42
        else:
            bx, by, br = W // 2, 300, 68
        pygame.draw.circle(self.pantalla, (40, 100, 190), (bx, by + 5), br)
        dibujar_bocina(self.pantalla, bx, by, br, AZUL)
        self.registrar(pygame.Rect(bx - br, by - br, 2 * br, 2 * br), lambda: self.voz.decir(r["audio"]))

        if r["tipo"] == "elegir":
            self.dibujar_elegir()
        else:
            self.dibujar_arrastrar(cat)

    def dibujar_elegir(self):
        r = self.ronda
        for i, (op, rect) in enumerate(zip(r["opciones"], self.rects_op)):
            pista = self.errores >= 2 and op == r["correcta"] and not self.resuelta
            fnt = self.f_gigante if len(op) <= 2 else self.f_palabra
            self.boton(rect, op, COLORES_FICHA[i % 5], lambda op=op: self.elegir(op), fnt, resaltar=pista)

    def dibujar_arrastrar(self, cat):
        for slot in self.slots:
            rect = slot["rect"]
            if slot["fijo"] or slot["lleno"]:
                continue
            pygame.draw.rect(self.pantalla, (245, 248, 255), rect, border_radius=22)
            pygame.draw.rect(self.pantalla, NEGRO, rect, 5, border_radius=22)
            if self.errores >= 2:
                texto_centrado(self.pantalla, slot["texto"], self.f_grande, (220, 225, 235), rect.center)
        for slot in self.slots:
            if slot["fijo"]:
                pygame.draw.rect(self.pantalla, cat["top"], slot["rect"], border_radius=22)
                pygame.draw.rect(self.pantalla, BLANCO, slot["rect"], 5, border_radius=22)
                texto_borde(self.pantalla, slot["texto"], self.f_grande, BLANCO, slot["rect"].center, g=2)
        for i, f in enumerate(self.fichas):
            if f is not self.arrastrando:
                self.dibujar_ficha(f, COLORES_FICHA[i % 5])
        if self.arrastrando:
            self.dibujar_ficha(self.arrastrando, COLORES_FICHA[self.fichas.index(self.arrastrando) % 5])

    def dibujar_ficha(self, f, color):
        oscuro = tuple(max(0, c - 70) for c in color)
        pygame.draw.rect(self.pantalla, oscuro, f["rect"].move(0, 6), border_radius=22)
        pygame.draw.rect(self.pantalla, color, f["rect"], border_radius=22)
        pygame.draw.rect(self.pantalla, BLANCO, f["rect"], 4, border_radius=22)
        texto_borde(self.pantalla, f["texto"], self.f_grande, BLANCO, f["rect"].center, g=2)

    # ---- resultados ------------------------------------------------------
    def pantalla_resultados(self):
        self.boton_volver(lambda: self.ir("niveles"))
        titulo_arcoiris(self.pantalla, "¡RESULTADOS!", self.f_titulo, (W // 2, 105))
        cinta = R(W // 2 - 190, 165, 380, 56)
        pygame.draw.rect(self.pantalla, (250, 235, 190), cinta, border_radius=10)
        pygame.draw.rect(self.pantalla, (150, 100, 50), cinta, 4, border_radius=10)
        texto_centrado(self.pantalla, "¡LO LOGRASTE!", self.f_med, NEGRO, cinta.center)
        self.personaje(0, 135, 470, 1.1, self.salto)
        self.personaje(1, 1190, 500, 0.8)
        # pergamino con actividades completadas
        perg = R(300, 245, 340, 290)
        pygame.draw.rect(self.pantalla, (245, 225, 170), perg, border_radius=18)
        pygame.draw.rect(self.pantalla, (150, 100, 50), perg, 6, border_radius=18)
        multilinea(self.pantalla, "ACTIVIDADES COMPLETADAS", self.f_peq, NEGRO, perg.centerx, perg.y + 18, perg.w - 30)
        for i, cat in enumerate(CATEGORIAS):
            hecha = any(self.estrellas_nivel(n) > 0 for n in cat["niveles"])
            y = perg.y + 120 + i * 50
            texto_centrado(self.pantalla, cat["nombre"].replace("SÍLABAS", "Sílabas").replace("LETRAS", "Letras").replace("PALABRAS", "Palabras"),
                           self.f_med, NEGRO, (perg.centerx - 25, y))
            col = VERDE if hecha else (200, 200, 200)
            pygame.draw.circle(self.pantalla, col, (perg.right - 50, y), 17)
            if hecha:
                pygame.draw.lines(self.pantalla, BLANCO, False, [(perg.right - 59, y), (perg.right - 52, y + 8), (perg.right - 40, y - 8)], 5)
        # estrellas
        for j in range(3):
            ok = j < self.estrellas_obtenidas
            dibujar_estrella(self.pantalla, 770 + j * 105, 340 + (-18 if j == 1 else 0), 50,
                             AMARILLO if ok else (225, 225, 225), (200, 150, 20) if ok else (175, 175, 175))
        e = self.estrellas_obtenidas
        texto_borde(self.pantalla, f"¡{e} ESTRELLA{'S' if e != 1 else ''} OBTENIDA{'S' if e != 1 else ''}!", self.f_peq, AMARILLO, (870, 440), g=3)
        self.boton(R(710, 475, 320, 85), "¡JUGAR OTRA VEZ!", VERDE, lambda: self.iniciar_nivel(self.nivel), self.f_peq)
        self.boton(R(710, 572, 320, 62), "Elegir actividad", NARANJA, lambda: self.ir("niveles"), self.f_peq)
        self.pie()

    # ---- bucle -----------------------------------------------------------
    def ejecutar(self):
        corriendo = True
        while corriendo:
            dt = self.reloj.tick(FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    corriendo = False
                else:
                    self.evento(e)
            self.actualizar(dt)
            self.dibujar()
        pygame.quit()


if __name__ == "__main__":
    Juego().ejecutar()
