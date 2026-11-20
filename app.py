"""
Conciliador BDV - verifica pagos recibidos en tu cuenta del Banco de Venezuela.

Uso:
  python app.py      -> abre el verificador en http://127.0.0.1:5000

Tus credenciales se leen del archivo .env (o se piden al arrancar) y
nunca salen de tu computadora.

Cómo trabaja (según la estructura real de BDVenlínea personas):
  1. Inicia sesión (usuario -> Entrar -> clave -> Entrar).
  2. En "Posición Consolidada" abre los Movimientos de la cuenta indicada.
  3. Escribe la referencia en el buscador "Buscar" del banco (filtra todos
     los movimientos, no solo la página visible).
  4. Lee la tabla: Fecha | Referencia | Descripción | Débito/Crédito | Monto | Saldo
     y busca un CRÉDITO con esa referencia y ese monto.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import getpass
import queue
import threading
import time
import webbrowser
import os
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import secrets
import socket
from functools import wraps

from flask import (Flask, abort, redirect, render_template, request, session,
                   url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE = Path(__file__).parent
DB = BASE / "historial.db"
PERFIL = BASE / "perfil_navegador"
LOGIN_URL = "https://bdvenlinea.banvenez.com/"
POSICION_URL = "https://bdvenlinea.banvenez.com/main/posicionconsolidada"

SECRETO = BASE / ".secreto_web"   # llave para firmar las sesiones de las cajeras

load_dotenv(BASE / ".env")
# Se llenan en cargar_credenciales() al arrancar (no al importar el módulo)
USUARIO = CLAVE = ""
CUENTA = os.getenv("BDV_CUENTA", "").strip()
SESION_MIN = float(os.getenv("BDV_SESION_MINUTOS") or "10")   # sesión abierta tras la última consulta
PING_SEG = float(os.getenv("BDV_PING_SEGUNDOS") or "90")       # cada cuánto "tocar" el banco
OCULTAR = os.getenv("BDV_OCULTAR_NAVEGADOR", "no").lower() in ("si", "sí", "true", "1")
ESCUCHAR_RED = os.getenv("BDV_ESCUCHAR_RED", "no").lower() in ("si", "sí", "true", "1")
PUERTO = int(os.getenv("BDV_PUERTO") or "5000")


def cargar_credenciales():
    """Lee usuario/clave/cuenta del .env o los pide en la ventana negra."""
    global USUARIO, CLAVE, CUENTA
    USUARIO = os.getenv("BDV_USUARIO") or input("Usuario BDV: ").strip()
    CLAVE = os.getenv("BDV_CLAVE") or getpass.getpass("Clave BDV (no se mostrará): ")
    CUENTA = CUENTA or input("Últimos 4 dígitos de la cuenta donde recibes pagos: ").strip()

# ---------------------------------------------------------------- utilidades

MIN_DIGITOS_REF = 6   # mínimo de dígitos de referencia para buscar


def a_numero(texto):
    """Convierte un monto escrito por la cajera o leído del banco a número.

    '-2.300,00 Bs.' -> -2300.0   '2.000' -> 2000.0   '2000,50' -> 2000.5
    '1250.5' -> 1250.5           '1,234.56' -> 1234.56
    Un punto seguido de exactamente 3 dígitos se toma como separador de miles
    (formato venezolano). La coma, si está, siempre es el decimal salvo que
    aparezca antes que un punto ('1,234.56').
    """
    t = re.sub(r"[^\d,.\-]", "", texto or "").strip(".,")
    if not re.search(r"\d", t):
        raise ValueError(f"Monto inválido: '{texto}'. Escríbelo así: 2000,00")
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):          # 2.300,00  (venezolano)
            t = t.replace(".", "").replace(",", ".")
        else:                                    # 2,300.00  (inglés)
            t = t.replace(",", "")
    elif "," in t:
        partes = t.split(",")
        if len(partes) > 2:                      # 1,000,000 -> miles
            t = t.replace(",", "")
        else:                                    # 2000,50 -> decimal
            t = t.replace(",", ".")
    elif "." in t:
        partes = t.split(".")
        if len(partes) > 2 or len(partes[1]) == 3:   # 2.000 / 1.000.000 -> miles
            t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        raise ValueError(f"Monto inválido: '{texto}'. Escríbelo así: 2000,00") from None


def solo_digitos(s):
    return re.sub(r"\D", "", s)


def sin_tildes(s):
    """'Sesión Inválida' -> 'sesion invalida' (para comparar textos del banco)."""
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def db():
    con = sqlite3.connect(DB, timeout=10)
    con.execute("""CREATE TABLE IF NOT EXISTS verificados(
        referencia TEXT, monto REAL, resultado TEXT, detalle TEXT, fecha TEXT)""")
    columnas = [c[1] for c in con.execute("PRAGMA table_info(verificados)")]
    if "cajera" not in columnas:                 # bases de datos de la versión anterior
        con.execute("ALTER TABLE verificados ADD COLUMN cajera TEXT DEFAULT ''")
    con.execute("""CREATE TABLE IF NOT EXISTS usuarios(
        usuario TEXT PRIMARY KEY COLLATE NOCASE, nombre TEXT, clave_hash TEXT,
        rol TEXT CHECK(rol IN ('admin','cajera')), activo INTEGER DEFAULT 1, creado TEXT)""")
    return con

# ---------------------------------------------------------------- navegador

class Banco:
    def __init__(self):
        self.pw = sync_playwright().start()
        ctx = None
        for channel in ("chrome", "msedge", None):
            try:
                opts = {"headless": OCULTAR, "viewport": {"width": 1366, "height": 800}}
                if channel:
                    opts["channel"] = channel
                ctx = self.pw.chromium.launch_persistent_context(str(PERFIL), **opts)
                break
            except Exception:
                continue
        if not ctx:
            raise RuntimeError("No se pudo iniciar el navegador. Asegúrate de tener Google Chrome o Microsoft Edge instalado.")
        self.ctx = ctx
        self.page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()

    # --- sesión
    def en_login(self):
        p = self.page
        if "/main/" in p.url:
            return False
        return (p.locator("input[type=text], #mat-input-0").count() > 0
                or p.locator("input[type=password]").count() > 0)

    def login(self):
        p = self.page
        if "/main/" in p.url:
            return
        p.goto(LOGIN_URL, wait_until="networkidle")
        if "/main/" in p.url:
            return
        print("-> Conectando con BDVenlinea...")
        p.wait_for_selector("input[type=text], #mat-input-0", timeout=20000)
        user_input = p.locator("input[type=text]").first
        user_input.fill(USUARIO)
        p.get_by_role("button", name=re.compile("entrar", re.I)).first.click()

        print("-> Ingresando contrasena...")
        p.wait_for_selector("input[type=password]", timeout=15000)
        pwd_input = p.locator("input[type=password]").first
        pwd_input.fill(CLAVE)
        p.get_by_role("button", name=re.compile("continuar", re.I)).first.click()

        print("-> Esperando respuesta del banco...")
        inicio = time.time()
        while time.time() - inicio < 45:
            p.wait_for_timeout(1000)
            if "/main/" in p.url:
                break
            snack = p.locator("mat-snack-bar-container, .mat-simple-snackbar")
            if snack.count() and snack.first.is_visible():
                txt = snack.first.inner_text().strip()
                norm = sin_tildes(txt)
                if "sesion activa" in norm:
                    raise RuntimeError("El banco indica: 'Cliente tiene una sesion activa'. Cierra la app BDV en tu telefono o espera unos minutos a que el banco la libere.")
                elif "bloquead" in norm:
                    raise RuntimeError("Tu usuario BDV se encuentra temporalmente bloqueado por el banco.")
                elif any(w in norm for w in ["invalid", "incorrect", "error"]):
                    raise RuntimeError(f"El banco indico: {txt}")
        else:
            if "/main/" not in p.url:
                raise RuntimeError("El banco tardo en responder o solicito verificacion extra (SMS/Ami Ven). Revisa la ventana de Chrome.")

        self.ultimo_uso = time.time()
        self.ultimo_ping = time.time()
        print("* Sesion iniciada correctamente")

    def logueado(self):
        return "/main/" in self.page.url and not self.en_login()

    def cerrar_sesion(self):
        p = self.page
        try:
            d = self.dialogo()
            if d.count() and d.first.is_visible():
                btn_reg = d.locator("button:has-text('Regresar')")
                if btn_reg.count() and btn_reg.first.is_visible():
                    btn_reg.first.click()
                else:
                    p.keyboard.press("Escape")
                p.wait_for_timeout(500)
            btn_salir = p.get_by_role("button", name=re.compile("salir", re.I))
            if btn_salir.count():
                btn_salir.first.click(timeout=5000)
                conf = p.get_by_role("button", name=re.compile("^(s[ií]|aceptar|confirmar|salir)$", re.I))
                try:
                    conf.last.click(timeout=3000)
                except Exception:
                    pass
                p.wait_for_timeout(1000)
        except Exception:
            pass
        print("* Sesion cerrada")

    def mantener_viva(self):
        """Hace una consulta liviana (reabrir movimientos) para que el banco no cierre la sesión."""
        try:
            print("-> [Ping] Manteniendo sesion activa en el banco...")
            self.abrir_movimientos()
            self.ultimo_ping = time.time()
        except Exception as e:
            print("[!] Aviso al mantener sesion:", e)

    # --- movimientos
    def dialogo(self):
        return self.page.locator("mat-dialog-container, [role=dialog]").filter(has_text=re.compile("movimientos", re.I))

    def abrir_movimientos(self):
        """Abre (o reabre, para traer datos frescos) el diálogo de movimientos."""
        p = self.page
        d = self.dialogo()
        if d.count() and d.first.is_visible():
            btn_reg = d.locator("button:has-text('Regresar')")
            if btn_reg.count() and btn_reg.first.is_visible():
                btn_reg.first.click()
            else:
                p.keyboard.press("Escape")
            p.wait_for_timeout(1000)

        if not self.logueado():
            self.login()

        fila = p.get_by_role("row").filter(has_text=CUENTA)
        fila.wait_for(timeout=15000)
        icon = fila.locator("mat-icon:has-text('subject')").first
        if not icon.count():
            icon = fila.locator("mat-icon").first
        icon.click()

        dlg = self.dialogo()
        dlg.wait_for(timeout=15000)
        dlg.locator("table, mat-table").wait_for(timeout=15000)
        p.wait_for_timeout(500)

    def buscar(self, referencia):
        d = self.dialogo()
        caja = d.locator("input").first
        caja.fill("")
        caja.fill(referencia)
        self.page.wait_for_timeout(800)
        filas = []
        filas_elem = d.locator("table tr, mat-table mat-row, mat-row").all()
        for r in filas_elem:
            celdas = [c.inner_text().strip() for c in r.locator("td, mat-cell, [role=gridcell]").all()]
            if len(celdas) >= 5:
                filas.append(celdas)
        return filas

# ---------------------------------------------------------------- verificación

def verificar(banco, referencia, monto):
    ref = solo_digitos(referencia)
    if len(ref) < MIN_DIGITOS_REF:
        return "ERROR", f"Escribe al menos {MIN_DIGITOS_REF} dígitos de la referencia (los últimos).", None
    print(f"\n[Verificando] Ref: {ref} | Monto: {monto:.2f} Bs.")
    for intento in range(2):
        try:
            if not banco.logueado():
                banco.login()
            banco.abrir_movimientos()
            filas = banco.buscar(ref)
            break
        except Exception as e:
            if intento or "sesion activa" in str(e).lower():
                raise
            print("[!] Reintentando conexion con el banco...")
            banco.login()
    banco.ultimo_uso = time.time()
    # celdas: Fecha, Referencia, Descripción, Débito/Crédito, Monto, Saldo
    # Solo cuenta si la referencia del banco TERMINA en los dígitos escritos
    # (o es exactamente igual). Así "123456" no coincide con "991234567".
    coinciden = [f for f in filas if solo_digitos(f[1]).endswith(ref)]
    creditos = [f for f in coinciden if "credito" in sin_tildes(f[3])]
    if not coinciden:
        return "NO_ENCONTRADO", "La referencia no aparece en los movimientos.", None
    if not creditos:
        f = coinciden[0]
        return "NO_ES_CREDITO", f"{f[0]} · {f[2]} · {f[3]} · {f[4]}", f[1]
    exactos = [f for f in creditos if abs(a_numero(f[4]) - monto) < 0.01]
    if len(exactos) == 1:
        f = exactos[0]
        return "APROBADO", f"{f[0]} · Ref {f[1]} · {f[2]} · {f[4]}", f[1]
    if len(exactos) > 1:
        refs = ", ".join(f[1] for f in exactos)
        return "VARIAS", f"Hay {len(exactos)} pagos con esos dígitos y ese monto ({refs}). Escribe la referencia completa.", None
    f = creditos[0]
    return "MONTO_DIFERENTE", f"En el banco: {f[4]} ({f[0]} · Ref {f[1]})", f[1]

# ---------------------------------------------------------------- interfaz web

TITULOS = {"APROBADO": "✅ Aprobado", "NO_ENCONTRADO": "❌ No encontrado",
           "NO_ES_CREDITO": "❌ La referencia existe pero no es un pago recibido",
           "MONTO_DIFERENTE": "⚠️ Referencia encontrada, pero el monto no coincide",
           "YA_USADA": "⚠️ Esta referencia ya fue aprobada antes",
           "VARIAS": "⚠️ Varios pagos coinciden: hace falta la referencia completa",
           "ERROR": "Error"}

ESPERA_MAX_SEG = 180          # una consulta puede esperar en cola detrás de otras cajeras
USUARIO_VALIDO = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
CLAVE_MIN = 6
INTENTOS_MAX = 5              # intentos fallidos de entrar antes de bloquear la IP
BLOQUEO_SEG = 300


class Trabajador(threading.Thread):
    """Todo lo de Playwright ocurre en este hilo. Las consultas de todas las
    cajeras entran a una cola y se atienden de una en una (una sola sesión del
    banco). Mantiene la sesión viva SESION_MIN minutos tras la última consulta."""
    def __init__(self):
        super().__init__(daemon=True)
        self.cola = queue.Queue()

    def consultar(self, ref, monto):
        resp = queue.Queue()
        self.cola.put((ref, monto, resp))
        try:
            ok, valor = resp.get(timeout=ESPERA_MAX_SEG)
        except queue.Empty:
            raise RuntimeError("El banco tardó demasiado en responder. Intenta de nuevo en unos momentos.")
        if not ok:
            raise valor
        return valor

    def solicitar_cierre(self):
        resp = queue.Queue()
        self.cola.put(("__CIERRE__", 0, resp))
        try:
            return resp.get(timeout=60)
        except queue.Empty:
            return False

    def detener(self):
        self.cola.put(None)
        self.join(timeout=20)

    def run(self):
        try:
            self.banco = Banco()
        except Exception as e:
            print("[!] No se pudo abrir el navegador:", e)
            while True:                          # responde el error en vez de colgarse
                item = self.cola.get()
                if item is None:
                    return
                item[2].put((False, RuntimeError(f"No se pudo abrir el navegador: {e}")))
        b = self.banco
        b.ultimo_uso = b.ultimo_ping = 0
        while True:
            try:
                item = self.cola.get(timeout=5)
            except queue.Empty:
                try:
                    if b.logueado():
                        if time.time() - b.ultimo_uso > SESION_MIN * 60:
                            print(f"-> [Inactividad] {SESION_MIN:g} min sin consultas: cerrando sesion en el banco...")
                            b.cerrar_sesion()
                        elif time.time() - b.ultimo_ping > PING_SEG:
                            b.mantener_viva()
                except Exception:
                    pass
                continue
            if item is None:                     # el programa se está cerrando
                if b.logueado():
                    b.cerrar_sesion()
                b.ctx.close()
                b.pw.stop()
                return
            if item[0] == "__CIERRE__":
                if b.logueado():
                    print("-> Cerrando sesion manual a peticion del administrador...")
                    b.cerrar_sesion()
                b.ultimo_uso = b.ultimo_ping = 0
                item[2].put(True)
                continue
            ref, monto, resp = item
            try:
                resp.put((True, verificar(b, ref, monto)))
            except Exception as e:
                resp.put((False, e))


# --- usuarios

def crear_usuario(con, usuario, nombre, clave, rol):
    usuario = usuario.strip()
    if not USUARIO_VALIDO.match(usuario):
        raise ValueError("El usuario debe tener de 3 a 30 letras, números, punto, guion o guion bajo (sin espacios).")
    if len(clave) < CLAVE_MIN:
        raise ValueError(f"La clave debe tener al menos {CLAVE_MIN} caracteres.")
    if rol not in ("admin", "cajera"):
        raise ValueError("Rol inválido.")
    if con.execute("SELECT 1 FROM usuarios WHERE usuario=?", (usuario,)).fetchone():
        raise ValueError(f"Ya existe el usuario '{usuario}'.")
    con.execute("INSERT INTO usuarios(usuario,nombre,clave_hash,rol,activo,creado) VALUES(?,?,?,?,1,?)",
                (usuario, nombre.strip() or usuario, generate_password_hash(clave), rol,
                 datetime.now().isoformat(timespec="seconds")))
    con.commit()


def hay_admin(con):
    return con.execute("SELECT 1 FROM usuarios WHERE rol='admin' AND activo=1").fetchone() is not None


def crear_admin_interactivo():
    """Pide en la ventana negra los datos de un administrador (o le cambia la clave si ya existe)."""
    print("\n=== Usuario administrador del Conciliador ===")
    print("Con este usuario entras a la página y creas los usuarios de las cajeras.\n")
    con = db()
    try:
        while True:
            usuario = input("Usuario administrador [admin]: ").strip() or "admin"
            clave = getpass.getpass(f"Clave (mínimo {CLAVE_MIN} caracteres, no se mostrará): ")
            if getpass.getpass("Repite la clave: ") != clave:
                print("[!] Las claves no coinciden. Intenta de nuevo.\n")
                continue
            existente = con.execute("SELECT usuario FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
            try:
                if existente:
                    if len(clave) < CLAVE_MIN:
                        raise ValueError(f"La clave debe tener al menos {CLAVE_MIN} caracteres.")
                    con.execute("UPDATE usuarios SET clave_hash=?, rol='admin', activo=1 WHERE usuario=?",
                                (generate_password_hash(clave), existente[0]))
                    con.commit()
                    print(f"* Clave actualizada; '{existente[0]}' es administrador y está activo.\n")
                else:
                    crear_usuario(con, usuario, "Administrador", clave, "admin")
                    print(f"* Administrador '{usuario}' creado.\n")
                return
            except ValueError as e:
                print(f"[!] {e}\n")
    finally:
        con.close()


# --- web

def llave_secreta():
    """Llave fija guardada en disco: así reiniciar el programa no saca a las cajeras."""
    try:
        return SECRETO.read_text().strip()
    except FileNotFoundError:
        llave = secrets.token_hex(32)
        SECRETO.write_text(llave)
        return llave


def ip_local():
    """IP de esta computadora en la red local (la que usan las cajeras)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))          # no envía nada; solo elige la interfaz
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return socket.gethostbyname(socket.gethostname())


def crear_app(trabajador):
    app = Flask(__name__, template_folder=str(BASE / "templates"))
    app.config.update(SECRET_KEY=llave_secreta(),
                      SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_HTTPONLY=True,
                      PERMANENT_SESSION_LIFETIME=12 * 3600)   # 12 h: un turno
    intentos = {}                 # ip -> [fallos, bloqueado_hasta]
    intentos_lock = threading.Lock()
    resultado_lock = threading.Lock()   # "ya usada" + guardado en un solo paso

    def usuario_actual():
        u = session.get("usuario")
        if not u:
            return None
        con = db()
        try:
            fila = con.execute("SELECT usuario, nombre, rol FROM usuarios WHERE usuario=? AND activo=1",
                               (u,)).fetchone()
        finally:
            con.close()
        if not fila:                         # desactivada mientras estaba conectada
            session.clear()
            return None
        return {"usuario": fila[0], "nombre": fila[1], "rol": fila[2]}

    def requiere_login(f):
        @wraps(f)
        def envoltura(*a, **k):
            if not usuario_actual():
                return redirect(url_for("entrar"))
            return f(*a, **k)
        return envoltura

    def requiere_admin(f):
        @wraps(f)
        def envoltura(*a, **k):
            u = usuario_actual()
            if not u:
                return redirect(url_for("entrar"))
            if u["rol"] != "admin":
                abort(403)
            return f(*a, **k)
        return envoltura

    @app.before_request
    def proteger_formularios():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        if request.method == "POST":
            enviado = request.form.get("csrf", "")
            if not secrets.compare_digest(enviado, session["csrf"]):
                abort(400, "Formulario vencido. Recarga la página e intenta de nuevo.")

    @app.context_processor
    def variables_comunes():
        return {"csrf": session.get("csrf", ""), "yo": usuario_actual(),
                "cuenta": CUENTA, "titulos": TITULOS, "min_ref": MIN_DIGITOS_REF}

    # --- entrar / salir
    @app.route("/entrar", methods=["GET", "POST"])
    def entrar():
        error = None
        ip = request.remote_addr or "?"
        if request.method == "POST":
            with intentos_lock:
                fallos, hasta = intentos.get(ip, [0, 0])
            if hasta > time.time():
                error = f"Demasiados intentos. Espera {int((hasta - time.time()) // 60) + 1} min."
            else:
                usuario = request.form.get("usuario", "").strip()
                clave = request.form.get("clave", "")
                con = db()
                try:
                    fila = con.execute("SELECT usuario, clave_hash FROM usuarios WHERE usuario=? AND activo=1",
                                       (usuario,)).fetchone()
                finally:
                    con.close()
                if fila and check_password_hash(fila[1], clave):
                    with intentos_lock:
                        intentos.pop(ip, None)
                    session.clear()
                    session.permanent = True
                    session["usuario"] = fila[0]
                    session["csrf"] = secrets.token_hex(16)
                    print(f"* {fila[0]} entró desde {ip}")
                    return redirect(url_for("index"))
                fallos += 1
                with intentos_lock:
                    intentos[ip] = [0, time.time() + BLOQUEO_SEG] if fallos >= INTENTOS_MAX else [fallos, 0]
                error = "Usuario o clave incorrectos."
                print(f"[!] Intento fallido de entrar como '{usuario}' desde {ip}")
        return render_template("entrar.html", error=error)

    @app.route("/salir", methods=["POST"])
    def salir():
        session.clear()
        return redirect(url_for("entrar"))

    # --- verificar
    @app.route("/", methods=["GET"])
    @requiere_login
    def index():
        yo = usuario_actual()
        ultimo = session.pop("ultimo", None)
        con = db()
        try:
            if yo["rol"] == "admin":
                hist = con.execute("SELECT fecha, referencia, monto, resultado, cajera FROM verificados "
                                   "ORDER BY fecha DESC LIMIT 50").fetchall()
            else:
                hist = con.execute("SELECT fecha, referencia, monto, resultado, cajera FROM verificados "
                                   "WHERE cajera=? ORDER BY fecha DESC LIMIT 20", (yo["usuario"],)).fetchall()
        finally:
            con.close()
        return render_template("index.html", ultimo=ultimo, hist=hist,
                               aviso=session.pop("aviso", None))

    @app.route("/verificar", methods=["POST"])
    @requiere_login
    def verificar_pago():
        yo = usuario_actual()
        ref = solo_digitos(request.form.get("referencia", ""))
        monto_txt = request.form.get("monto", "")
        try:
            monto = a_numero(monto_txt)
            if monto <= 0:
                raise ValueError("El monto debe ser mayor que cero.")
            print(f"[{yo['usuario']}] consulta ref {ref} por {monto:.2f}")
            res, detalle, ref_banco = trabajador.consultar(ref, monto)
            con = db()
            try:
                with resultado_lock:
                    if res == "APROBADO":
                        previo = con.execute("SELECT fecha, cajera FROM verificados WHERE resultado='APROBADO' "
                                             "AND referencia=?", (ref_banco,)).fetchone()
                        if previo:
                            res = "YA_USADA"
                            quien = f" por {previo[1]}" if previo[1] else ""
                            detalle = f"Ya se aprobó el {previo[0][:16].replace('T', ' ')}{quien} · {detalle}"
                        else:
                            ref = ref_banco      # se guarda la referencia completa del banco
                    con.execute("INSERT INTO verificados(referencia,monto,resultado,detalle,fecha,cajera) "
                                "VALUES(?,?,?,?,?,?)",
                                (ref, monto, res, detalle, datetime.now().isoformat(), yo["usuario"]))
                    con.commit()
            finally:
                con.close()
        except Exception as e:
            res, detalle = "ERROR", str(e)
        session["ultimo"] = {"res": res, "detalle": detalle, "ref": ref, "monto": monto_txt}
        return redirect(url_for("index"))     # recargar la página no repite la consulta

    @app.route("/cerrar-banco", methods=["POST"])
    @requiere_admin
    def cerrar_banco():
        trabajador.solicitar_cierre()
        session["aviso"] = "Sesión del banco cerrada. La próxima consulta vuelve a entrar."
        return redirect(url_for("index"))

    # --- administración de usuarios
    @app.route("/usuarios", methods=["GET"])
    @requiere_admin
    def usuarios():
        con = db()
        try:
            lista = con.execute("SELECT usuario, nombre, rol, activo, creado FROM usuarios "
                                "ORDER BY activo DESC, rol, usuario").fetchall()
        finally:
            con.close()
        return render_template("usuarios.html", lista=lista,
                               aviso=session.pop("aviso", None), error=session.pop("error", None))

    @app.route("/usuarios/nuevo", methods=["POST"])
    @requiere_admin
    def usuario_nuevo():
        con = db()
        try:
            f = request.form
            crear_usuario(con, f.get("usuario", ""), f.get("nombre", ""), f.get("clave", ""),
                          f.get("rol", "cajera"))
            session["aviso"] = f"Usuario '{f.get('usuario', '').strip()}' creado."
        except ValueError as e:
            session["error"] = str(e)
        finally:
            con.close()
        return redirect(url_for("usuarios"))

    @app.route("/usuarios/<usuario>/clave", methods=["POST"])
    @requiere_admin
    def usuario_clave(usuario):
        clave = request.form.get("clave", "")
        if len(clave) < CLAVE_MIN:
            session["error"] = f"La clave debe tener al menos {CLAVE_MIN} caracteres."
        else:
            con = db()
            try:
                n = con.execute("UPDATE usuarios SET clave_hash=? WHERE usuario=?",
                                (generate_password_hash(clave), usuario)).rowcount
                con.commit()
            finally:
                con.close()
            session["aviso" if n else "error"] = (f"Clave de '{usuario}' cambiada." if n
                                                  else "Ese usuario no existe.")
        return redirect(url_for("usuarios"))

    @app.route("/usuarios/<usuario>/activo", methods=["POST"])
    @requiere_admin
    def usuario_activo(usuario):
        yo = usuario_actual()
        activar = request.form.get("activo") == "1"
        if usuario.lower() == yo["usuario"].lower() and not activar:
            session["error"] = "No puedes desactivar tu propio usuario."
        else:
            con = db()
            try:
                con.execute("UPDATE usuarios SET activo=? WHERE usuario=?", (1 if activar else 0, usuario))
                con.commit()
            finally:
                con.close()
            session["aviso"] = f"Usuario '{usuario}' {'activado' if activar else 'desactivado'}."
        return redirect(url_for("usuarios"))

    @app.errorhandler(403)
    def prohibido(e):
        return render_template("mensaje.html", titulo="Sin permiso",
                               texto="Esta página es solo para el administrador."), 403

    @app.errorhandler(400)
    def mala_peticion(e):
        return render_template("mensaje.html", titulo="Formulario vencido",
                               texto=getattr(e, "description", "Recarga la página e intenta de nuevo.")), 400

    return app


def main():
    parser = argparse.ArgumentParser(description="Conciliador BDV")
    parser.add_argument("--nuevo-admin", action="store_true",
                        help="crea un administrador o le cambia la clave (si la olvidaste) y sale")
    args = parser.parse_args()

    con = db()
    try:
        falta_admin = not hay_admin(con)
    finally:
        con.close()
    if args.nuevo_admin:
        crear_admin_interactivo()
        return
    if falta_admin:
        crear_admin_interactivo()

    cargar_credenciales()
    trabajador = Trabajador()
    trabajador.start()
    app = crear_app(trabajador)

    host = "0.0.0.0" if ESCUCHAR_RED else "127.0.0.1"
    print(f"\n[OK] Conciliador BDV funcionando")
    print(f"  En esta computadora:  http://127.0.0.1:{PUERTO}")
    if ESCUCHAR_RED:
        print(f"  Para las cajeras:     http://{ip_local()}:{PUERTO}")
    else:
        print("  (Solo esta computadora. Para las cajeras pon BDV_ESCUCHAR_RED=si en el .env)")
    print(f"  Sesión del banco: se abre en la primera consulta, se mantiene viva y se cierra")
    print(f"  sola tras {SESION_MIN:g} min sin consultas. Deja esta ventana abierta.")
    print("  Para apagar el programa: Ctrl+C (cierra la sesión del banco antes de salir).\n")
    threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{PUERTO}")).start()
    try:
        from waitress import serve
        serve(app, host=host, port=PUERTO, threads=8, channel_timeout=ESPERA_MAX_SEG + 60)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nCerrando sesión del banco...")
        trabajador.detener()


if __name__ == "__main__":
    main()
