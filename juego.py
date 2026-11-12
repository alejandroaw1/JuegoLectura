"""
Letras Brainrot - Primera versión (prototipo)
Videojuego educativo 2D para preescolar: aprender cómo suenan las sílabas y formarlas.

Actividades:
  1) ESCUCHA : suena una sílaba y el niño toca la opción correcta.
  2) FORMA   : suena una sílaba y el niño arrastra las letras a los espacios vacíos.

Ejecutar:  python juego.py
"""
import json
import math
import os
import random
import threading
from array import array

import pygame

# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------
W, H = 1100, 700
FPS = 60
BASE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE, "assets", "audio")
SAVE_FILE = os.path.join(BASE, "progreso.json")

# Cada etapa introduce una consonante nueva combinada con las 5 vocales.
ETAPAS = [
    {"nombre": "Mundo de la M", "silabas": ["MA", "ME", "MI", "MO", "MU"]},
    {"nombre": "Mundo de la P", "silabas": ["PA", "PE", "PI", "PO", "PU"]},
    {"nombre": "Mundo de la L", "silabas": ["LA", "LE", "LI", "LO", "LU"]},
    {"nombre": "Mundo de la S", "silabas": ["SA", "SE", "SI", "SO", "SU"]},
]
LETRAS_DISTRACTORAS = "MPLSTNDAEIOU"

# Colores
BLANCO = (255, 255, 255)
NEGRO = (30, 30, 40)
FONDO_TOP = (150, 220, 255)
FONDO_BOT = (255, 240, 190)
AMARILLO = (255, 205, 60)
VERDE = (90, 200, 120)
ROJO = (235, 90, 90)
AZUL = (80, 150, 240)
MORADO = (160, 110, 220)
NARANJA = (255, 150, 60)
ROSA = (255, 140, 190)
COLORES_OPCION = [AZUL, NARANJA, MORADO, ROSA]


# --------------------------------------------------------------------------
# Audio: voz (archivos .ogg/.wav/.mp3 o, si no existen, texto a voz) y efectos
# --------------------------------------------------------------------------
class Voz:
    """Reproduce el sonido de una sílaba.
    1) Busca assets/audio/<silaba>.ogg|wav|mp3  (lo ideal: voz real grabada)
    2) Si no existe, intenta pyttsx3 (voz del sistema, sin internet)
    """

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
            ruta = os.path.join(AUDIO_DIR, f"{texto.lower()}.{ext}")
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
    """Genera un sonido corto (efectos de acierto/error) sin necesidad de archivos."""
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
# Personajes (dibujados con formas simples; se pueden cambiar por sprites PNG)
# --------------------------------------------------------------------------
def dibujar_tung(s, cx, cy, k, t, salto=0):
    cy += math.sin(t * 6) * 4 * k - salto
    # bate
    pygame.draw.line(s, (110, 65, 30), (cx + 55 * k, cy + 20 * k), (cx + 105 * k, cy - 80 * k), max(2, int(14 * k)))
    # piernas
    for dx in (-25, 25):
        pygame.draw.rect(s, (140, 90, 45), (cx + (dx - 8) * k, cy + 70 * k, 16 * k, 40 * k), border_radius=6)
        pygame.draw.ellipse(s, NEGRO, (cx + (dx - 16) * k, cy + 100 * k, 34 * k, 16 * k))
    # tronco
    cuerpo = pygame.Rect(0, 0, 120 * k, 180 * k)
    cuerpo.center = (cx, cy)
    pygame.draw.rect(s, (176, 112, 56), cuerpo, border_radius=int(45 * k))
    pygame.draw.rect(s, (120, 75, 35), cuerpo, 4, border_radius=int(45 * k))
    # anillos de madera
    pygame.draw.ellipse(s, (130, 80, 40), (cx - 28 * k, cy - 82 * k, 56 * k, 22 * k), 3)
    # brazo con bate
    pygame.draw.line(s, (140, 90, 45), (cx + 50 * k, cy + 5 * k), (cx + 75 * k, cy - 5 * k), max(2, int(12 * k)))
    # ojos
    for dx in (-24, 24):
        pygame.draw.circle(s, BLANCO, (cx + dx * k, cy - 25 * k), int(19 * k))
        pygame.draw.circle(s, NEGRO, (cx + dx * k, cy - 25 * k), int(8 * k))
    # boca
    pygame.draw.ellipse(s, (90, 30, 30), (cx - 22 * k, cy + 8 * k, 44 * k, 30 * k))
    pygame.draw.ellipse(s, (240, 120, 120), (cx - 12 * k, cy + 22 * k, 24 * k, 14 * k))


def dibujar_tralalero(s, cx, cy, k, t, salto=0):
    cy += math.sin(t * 5 + 1) * 4 * k - salto
    # aleta
    pygame.draw.polygon(s, (70, 110, 160), [(cx - 10 * k, cy - 70 * k), (cx + 30 * k, cy - 120 * k), (cx + 40 * k, cy - 60 * k)])
    # patas con tenis
    for dx in (-45, 0, 45):
        pygame.draw.rect(s, (90, 140, 190), (cx + (dx - 8) * k, cy + 55 * k, 16 * k, 45 * k))
        pygame.draw.ellipse(s, ROJO, (cx + (dx - 22) * k, cy + 92 * k, 46 * k, 22 * k))
        pygame.draw.ellipse(s, BLANCO, (cx + (dx - 22) * k, cy + 106 * k, 46 * k, 8 * k))
    # cuerpo
    pygame.draw.ellipse(s, (95, 150, 200), (cx - 100 * k, cy - 70 * k, 200 * k, 140 * k))
    pygame.draw.ellipse(s, (210, 230, 245), (cx - 70 * k, cy - 5 * k, 150 * k, 65 * k))
    # ojo y boca
    pygame.draw.circle(s, BLANCO, (cx + 55 * k, cy - 25 * k), int(17 * k))
    pygame.draw.circle(s, NEGRO, (cx + 60 * k, cy - 25 * k), int(7 * k))
    pygame.draw.arc(s, NEGRO, (cx + 20 * k, cy - 5 * k, 80 * k, 40 * k), math.pi, 2 * math.pi, 4)


def dibujar_ballerina(s, cx, cy, k, t, salto=0):
    cy += math.sin(t * 5 + 2) * 5 * k - salto
    # piernas
    for dx in (-14, 14):
        pygame.draw.line(s, (250, 215, 190), (cx + dx * k, cy + 50 * k), (cx + dx * 1.4 * k, cy + 115 * k), max(2, int(9 * k)))
        pygame.draw.ellipse(s, ROSA, (cx + (dx * 1.4 - 12) * k, cy + 110 * k, 26 * k, 12 * k))
    # tutú
    pygame.draw.ellipse(s, ROSA, (cx - 70 * k, cy + 20 * k, 140 * k, 50 * k))
    # torso
    pygame.draw.rect(s, (255, 180, 215), (cx - 22 * k, cy - 30 * k, 44 * k, 60 * k), border_radius=14)
    # brazos
    pygame.draw.line(s, (250, 215, 190), (cx - 20 * k, cy - 20 * k), (cx - 60 * k, cy - 60 * k), max(2, int(8 * k)))
    pygame.draw.line(s, (250, 215, 190), (cx + 20 * k, cy - 20 * k), (cx + 60 * k, cy - 60 * k), max(2, int(8 * k)))
    # cabeza = taza de capuchino
    pygame.draw.circle(s, (150, 95, 55), (cx, cy - 75 * k), int(48 * k))
    pygame.draw.ellipse(s, (250, 240, 225), (cx - 38 * k, cy - 112 * k, 76 * k, 30 * k))
    pygame.draw.circle(s, (150, 95, 55), (cx, cy - 98 * k), int(6 * k))
    for dx in (-17, 17):
        pygame.draw.circle(s, BLANCO, (cx + dx * k, cy - 68 * k), int(11 * k))
        pygame.draw.circle(s, NEGRO, (cx + dx * k, cy - 68 * k), int(5 * k))
    pygame.draw.arc(s, BLANCO, (cx - 16 * k, cy - 62 * k, 32 * k, 24 * k), math.pi, 2 * math.pi, 3)


PERSONAJES = [
    ("Tung Tung Sahur", dibujar_tung),
    ("Tralalero Tralala", dibujar_tralalero),
    ("Ballerina Cappuccina", dibujar_ballerina),
]


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def fuente(tam, negrita=True):
    for nombre in ("comicsansms", "arialrounded", "verdana", "arial"):
        ruta = pygame.font.match_font(nombre, bold=negrita)
        if ruta:
            return pygame.font.Font(ruta, tam)
    return pygame.font.Font(None, tam)


def fondo_degradado(surf):
    for y in range(0, H, 4):
        f = y / H
        c = tuple(int(FONDO_TOP[i] * (1 - f) + FONDO_BOT[i] * f) for i in range(3))
        pygame.draw.rect(surf, c, (0, y, W, 4))


def texto_centrado(surf, texto, fnt, color, centro):
    img = fnt.render(texto, True, color)
    surf.blit(img, img.get_rect(center=centro))


def cargar_progreso():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            datos = json.load(f)
        est = datos.get("estrellas", [])
        return (est + [0] * len(ETAPAS))[: len(ETAPAS)]
    except Exception:
        return [0] * len(ETAPAS)


def guardar_progreso(estrellas):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"estrellas": estrellas}, f)
    except OSError:
        pass


def dibujar_estrella(surf, cx, cy, r, color):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, (200, 150, 20), pts, 3)


def dibujar_bocina(surf, cx, cy, r, color):
    pygame.draw.circle(surf, color, (cx, cy), r)
    pygame.draw.circle(surf, BLANCO, (cx, cy), r, 4)
    pygame.draw.polygon(surf, BLANCO, [(cx - 22, cy - 10), (cx - 8, cy - 10), (cx + 12, cy - 28),
                                       (cx + 12, cy + 28), (cx - 8, cy + 10), (cx - 22, cy + 10)])
    pygame.draw.arc(surf, BLANCO, (cx - 4, cy - 20, 40, 40), -0.9, 0.9, 5)
    pygame.draw.arc(surf, BLANCO, (cx - 12, cy - 32, 60, 64), -0.9, 0.9, 5)


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
        pygame.display.set_caption("Letras Brainrot")
        self.reloj = pygame.time.Clock()
        self.f_titulo = fuente(80)
        self.f_gigante = fuente(120)
        self.f_grande = fuente(64)
        self.f_med = fuente(40)
        self.f_peq = fuente(28)
        self.voz = Voz()
        self.sfx_ok = crear_tono([523, 659, 784], 0.12)
        self.sfx_mal = crear_tono([260, 200], 0.15)
        self.estrellas_guardadas = cargar_progreso()
        self.estado = "menu"
        self.botones = []
        self.particulas = []
        self.t = 0.0
        self.salto = 0.0
        self.mensaje = ""
        self.t_mensaje = 0
        self.t_auto = None
        self.t_siguiente = None
        self.arrastrando = None

    # ---- flujo -----------------------------------------------------------
    def iniciar_etapa(self, i):
        self.etapa = i
        silabas = ETAPAS[i]["silabas"][:]
        random.shuffle(silabas)
        self.rondas = [("escucha", s) for s in silabas] + [("formar", s) for s in silabas]
        self.ronda_i = 0
        self.estrellas = 0
        self.estado = "juego"
        self.nueva_ronda()

    def nueva_ronda(self):
        self.tipo, self.silaba = self.rondas[self.ronda_i]
        self.errores = 0
        self.resuelta = False
        self.t_siguiente = None
        self.arrastrando = None
        self.t_auto = pygame.time.get_ticks() + 700
        if self.tipo == "escucha":
            pool = [s for s in ETAPAS[self.etapa]["silabas"] if s != self.silaba]
            opciones = random.sample(pool, 2) + [self.silaba]
            random.shuffle(opciones)
            self.opciones = opciones
            self.decir_mensaje("¡Escucha con atención!")
        else:
            self.slots = []
            for i, letra in enumerate(self.silaba):
                x = W // 2 - 170 + i * 190
                self.slots.append({"rect": pygame.Rect(x, 300, 160, 180), "letra": letra, "lleno": False})
            extras = [c for c in LETRAS_DISTRACTORAS if c not in self.silaba]
            letras = list(self.silaba) + random.sample(extras, 2)
            random.shuffle(letras)
            self.fichas = []
            for i, letra in enumerate(letras):
                x = W // 2 - 2 * 150 + 10 + i * 150
                r = pygame.Rect(x, 540, 130, 130)
                self.fichas.append({"letra": letra, "rect": r, "casa": r.copy(), "colocada": False})
            self.decir_mensaje("¡Arrastra las letras!")

    def decir_mensaje(self, texto, dur=2500):
        self.mensaje = texto
        self.t_mensaje = pygame.time.get_ticks() + dur

    def acierto(self):
        if self.resuelta:
            return
        self.resuelta = True
        self.estrellas += 1
        self.salto = 40
        reproducir(self.sfx_ok)
        self.decir_mensaje("¡Muy bien!", 1600)
        self.confeti(W // 2, 250)
        self.t_siguiente = pygame.time.get_ticks() + 1700

    def fallo(self):
        self.errores += 1
        reproducir(self.sfx_mal)
        self.decir_mensaje("¡Inténtalo otra vez!", 1500)
        self.t_auto = pygame.time.get_ticks() + 500  # repite el sonido como pista

    def avanzar(self):
        self.ronda_i += 1
        if self.ronda_i >= len(self.rondas):
            self.estado = "fin"
            self.estrellas_guardadas[self.etapa] = max(self.estrellas_guardadas[self.etapa], self.estrellas)
            guardar_progreso(self.estrellas_guardadas)
            reproducir(self.sfx_ok)
            for _ in range(4):
                self.confeti(random.randint(200, 900), 200)
        else:
            self.nueva_ronda()

    def confeti(self, x, y):
        for _ in range(40):
            ang = random.uniform(0, 2 * math.pi)
            vel = random.uniform(2, 8)
            self.particulas.append([x, y, math.cos(ang) * vel, math.sin(ang) * vel - 3,
                                    random.choice([AMARILLO, ROSA, AZUL, VERDE, NARANJA]), 70])

    # ---- entrada ---------------------------------------------------------
    def evento(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, accion in self.botones:
                if rect.collidepoint(e.pos):
                    accion()
                    return
            if self.estado == "juego" and self.tipo == "formar" and not self.resuelta:
                for ficha in reversed(self.fichas):
                    if not ficha["colocada"] and ficha["rect"].collidepoint(e.pos):
                        self.arrastrando = ficha
                        ficha["dx"] = ficha["rect"].x - e.pos[0]
                        ficha["dy"] = ficha["rect"].y - e.pos[1]
                        break
        elif e.type == pygame.MOUSEMOTION and self.arrastrando:
            f = self.arrastrando
            f["rect"].x = e.pos[0] + f["dx"]
            f["rect"].y = e.pos[1] + f["dy"]
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.arrastrando:
            self.soltar_ficha(self.arrastrando)
            self.arrastrando = None

    def soltar_ficha(self, ficha):
        centro = ficha["rect"].center
        for slot in self.slots:
            if slot["rect"].collidepoint(centro) and not slot["lleno"]:
                if slot["letra"] == ficha["letra"]:
                    ficha["rect"].center = slot["rect"].center
                    ficha["colocada"] = True
                    slot["lleno"] = True
                    reproducir(self.sfx_ok)
                    if all(s["lleno"] for s in self.slots):
                        self.acierto()
                        self.t_auto = pygame.time.get_ticks() + 400
                    return
                break
        ficha["rect"] = ficha["casa"].copy()
        if any(slot["rect"].collidepoint(centro) for slot in self.slots):
            self.fallo()

    def elegir_opcion(self, s):
        if self.resuelta:
            return
        if s == self.silaba:
            self.acierto()
        else:
            self.fallo()

    # ---- actualización ---------------------------------------------------
    def actualizar(self, dt):
        self.t += dt
        ahora = pygame.time.get_ticks()
        if self.salto > 0:
            self.salto = max(0, self.salto - 80 * dt)
        if self.estado == "juego":
            if self.t_auto and ahora >= self.t_auto:
                self.t_auto = None
                self.voz.decir(self.silaba)
            if self.t_siguiente and ahora >= self.t_siguiente:
                self.t_siguiente = None
                self.avanzar()
        for p in self.particulas:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.25
            p[5] -= 1
        self.particulas = [p for p in self.particulas if p[5] > 0]

    # ---- dibujo ----------------------------------------------------------
    def boton(self, rect, texto, color, accion, fnt=None, resaltar=False):
        mouse = pygame.mouse.get_pos()
        r = rect.copy()
        if rect.collidepoint(mouse):
            r.inflate_ip(8, 8)
        sombra = r.move(0, 6)
        pygame.draw.rect(self.pantalla, tuple(max(0, c - 70) for c in color), sombra, border_radius=28)
        pygame.draw.rect(self.pantalla, color, r, border_radius=28)
        if resaltar:
            pygame.draw.rect(self.pantalla, AMARILLO, r.inflate(14, 14), 6, border_radius=34)
        texto_centrado(self.pantalla, texto, fnt or self.f_med, BLANCO, r.center)
        self.botones.append((rect, accion))

    def personaje(self, x, y, k=1.0, idx=None):
        idx = self.etapa % len(PERSONAJES) if idx is None else idx
        PERSONAJES[idx][1](self.pantalla, x, y, k, self.t, self.salto)

    def globo(self, x, y):
        if pygame.time.get_ticks() > self.t_mensaje or not self.mensaje:
            return
        img = self.f_peq.render(self.mensaje, True, NEGRO)
        r = img.get_rect(center=(x, y)).inflate(40, 26)
        pygame.draw.rect(self.pantalla, BLANCO, r, border_radius=20)
        pygame.draw.rect(self.pantalla, NEGRO, r, 3, border_radius=20)
        pygame.draw.polygon(self.pantalla, BLANCO, [(r.centerx - 15, r.bottom - 2), (r.centerx + 15, r.bottom - 2), (r.centerx - 25, r.bottom + 24)])
        self.pantalla.blit(img, img.get_rect(center=r.center))

    def dibujar(self):
        self.botones = []
        fondo_degradado(self.pantalla)
        getattr(self, f"pantalla_{self.estado}")()
        for x, y, _, _, c, vida in self.particulas:
            pygame.draw.rect(self.pantalla, c, (x, y, 10, 10))
        pygame.display.flip()

    def pantalla_menu(self):
        texto_centrado(self.pantalla, "Letras Brainrot", self.f_titulo, (200, 60, 120), (W // 2, 110))
        texto_centrado(self.pantalla, "¡Aprende a leer jugando!", self.f_med, NEGRO, (W // 2, 190))
        for i, (nombre, fn) in enumerate(PERSONAJES):
            fn(self.pantalla, 250 + i * 300, 400, 1.0, self.t)
        self.boton(pygame.Rect(W // 2 - 160, 540, 320, 110), "¡Jugar!", VERDE, lambda: setattr(self, "estado", "etapas"), self.f_grande)

    def pantalla_etapas(self):
        texto_centrado(self.pantalla, "Elige un mundo", self.f_titulo, (200, 60, 120), (W // 2, 90))
        for i, e in enumerate(ETAPAS):
            col, fila = i % 2, i // 2
            r = pygame.Rect(120 + col * 460, 200 + fila * 200, 420, 160)
            self.boton(r, e["nombre"], COLORES_OPCION[i % 4], lambda i=i: self.iniciar_etapa(i))
            texto_centrado(self.pantalla, f"★ {self.estrellas_guardadas[i]} / 10", self.f_peq, AMARILLO, (r.centerx, r.bottom - 28))
        self.boton(pygame.Rect(30, 620, 200, 60), "Volver", ROJO, lambda: setattr(self, "estado", "menu"), self.f_peq)

    def cabecera_juego(self):
        self.boton(pygame.Rect(20, 20, 130, 55), "Salir", ROJO, lambda: setattr(self, "estado", "etapas"), self.f_peq)
        texto_centrado(self.pantalla, ETAPAS[self.etapa]["nombre"], self.f_peq, NEGRO, (W // 2 - 130, 45))
        # barra de progreso con estrellas
        for i in range(len(self.rondas)):
            color = AMARILLO if i < self.ronda_i or (i == self.ronda_i and self.resuelta) else (220, 220, 220)
            dibujar_estrella(self.pantalla, W - 40 - (len(self.rondas) - 1 - i) * 40, 45, 16, color)
        bocina = pygame.Rect(W // 2 - 55, 100, 110, 110)
        self.botones.append((bocina, lambda: self.voz.decir(self.silaba)))
        dibujar_bocina(self.pantalla, bocina.centerx, bocina.centery, 52, AZUL)

    def pantalla_juego(self):
        self.cabecera_juego()
        self.personaje(170, 380, 0.9)
        self.globo(300, 190)
        if self.tipo == "escucha":
            self.dibujar_escucha()
        else:
            self.dibujar_formar()

    def dibujar_escucha(self):
        texto_centrado(self.pantalla, "¿Qué sílaba escuchaste?", self.f_med, NEGRO, (W // 2, 270))
        for i, s in enumerate(self.opciones):
            r = pygame.Rect(W // 2 - 330 + i * 230, 360, 210, 210)
            pista = self.errores >= 2 and s == self.silaba
            self.boton(r, s, COLORES_OPCION[i], lambda s=s: self.elegir_opcion(s), self.f_gigante, resaltar=pista)

    def dibujar_formar(self):
        texto_centrado(self.pantalla, "Forma la sílaba que escuchaste", self.f_med, NEGRO, (W // 2 + 60, 265))
        for slot in self.slots:
            pygame.draw.rect(self.pantalla, BLANCO, slot["rect"], border_radius=24)
            pygame.draw.rect(self.pantalla, NEGRO, slot["rect"], 5, border_radius=24)
            if self.errores >= 2 and not slot["lleno"]:  # pista: letra tenue
                img = self.f_gigante.render(slot["letra"], True, (225, 225, 225))
                self.pantalla.blit(img, img.get_rect(center=slot["rect"].center))
        colores = {}
        for i, f in enumerate(self.fichas):
            colores[id(f)] = COLORES_OPCION[i % 4]
        for f in self.fichas:
            if f is self.arrastrando:
                continue
            self.dibujar_ficha(f, colores[id(f)])
        if self.arrastrando:
            self.dibujar_ficha(self.arrastrando, colores[id(self.arrastrando)])

    def dibujar_ficha(self, f, color):
        pygame.draw.rect(self.pantalla, color, f["rect"], border_radius=22)
        pygame.draw.rect(self.pantalla, BLANCO, f["rect"], 4, border_radius=22)
        texto_centrado(self.pantalla, f["letra"], self.f_grande, BLANCO, f["rect"].center)

    def pantalla_fin(self):
        texto_centrado(self.pantalla, "¡Lo lograste!", self.f_titulo, (200, 60, 120), (W // 2, 120))
        self.personaje(W // 2, 400, 1.3)
        texto_centrado(self.pantalla, f"Ganaste {self.estrellas} estrellas", self.f_grande, NEGRO, (W // 2, 230))
        self.boton(pygame.Rect(W // 2 - 380, 570, 340, 90), "Jugar otra vez", VERDE, lambda: self.iniciar_etapa(self.etapa), self.f_med)
        self.boton(pygame.Rect(W // 2 + 40, 570, 340, 90), "Otros mundos", AZUL, lambda: setattr(self, "estado", "etapas"), self.f_med)

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
