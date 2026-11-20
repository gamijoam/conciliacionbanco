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
from flask import Flask, render_template_string, request, redirect
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE = Path(__file__).parent
DB = BASE / "historial.db"
PERFIL = BASE / "perfil_navegador"
LOGIN_URL = "https://bdvenlinea.banvenez.com/"
POSICION_URL = "https://bdvenlinea.banvenez.com/main/posicionconsolidada"

load_dotenv(BASE / ".env")
USUARIO = os.getenv("BDV_USUARIO") or input("Usuario BDV: ").strip()
CLAVE = os.getenv("BDV_CLAVE") or getpass.getpass("Clave BDV (no se mostrará): ")
CUENTA = os.getenv("BDV_CUENTA", "").strip() or input(
    "Últimos 4 dígitos de la cuenta donde recibes pagos: ").strip()
SESION_MIN = float(os.getenv("BDV_SESION_MINUTOS") or "10")   # sesión abierta tras la última consulta
PING_SEG = float(os.getenv("BDV_PING_SEGUNDOS") or "90")       # cada cuánto "tocar" el banco
OCULTAR = os.getenv("BDV_OCULTAR_NAVEGADOR", "no").lower() in ("si", "sí", "true", "1")

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
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS verificados(
        referencia TEXT, monto REAL, resultado TEXT, detalle TEXT, fecha TEXT)""")
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

HTML = """
<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Conciliador BDV</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:680px;margin:40px auto;padding:0 16px;color:#1d1d1f}
 h1{font-size:22px} form{display:flex;gap:8px;flex-wrap:wrap}
 input{padding:10px;font-size:16px;border:1px solid #ccc;border-radius:8px;flex:1;min-width:150px}
 button{padding:10px 18px;font-size:16px;border:0;border-radius:8px;background:#0057b8;color:#fff;cursor:pointer}
 .r{margin-top:20px;padding:16px;border-radius:10px;font-size:18px}
 .APROBADO{background:#e6f6ea;color:#14632b}.NO_ENCONTRADO,.NO_ES_CREDITO{background:#fde8e8;color:#8a1c1c}
 .MONTO_DIFERENTE,.YA_USADA,.VARIAS{background:#fff4dc;color:#7a5200}.ERROR{background:#eee}
 small{display:block;margin-top:6px;font-size:13px;opacity:.85}
 table{width:100%;margin-top:28px;border-collapse:collapse;font-size:14px}
 td,th{padding:6px;border-bottom:1px solid #eee;text-align:left}
</style></head><body>
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
 <h1>Conciliador BDV · cuenta ***{{cuenta}}</h1>
 <a href="/cerrar" onclick="return confirm('¿Deseas cerrar la sesión en el Banco de Venezuela ahora?')" style="font-size:13px; color:#d93025; text-decoration:none; padding:6px 12px; border:1px solid #d93025; border-radius:6px; font-weight:500;">Cerrar sesión BDV</a>
</div>
<form method="post" onsubmit="var btn=document.getElementById('btnSubmit'); btn.disabled=true; btn.innerText='⏳ Verificando con BDV...';">
 <input name="referencia" placeholder="Referencia (completa o últimos 6+ dígitos)" required autofocus>
 <input name="monto" placeholder="Monto (ej. 2000,00)" required>
 <button id="btnSubmit">Verificar</button>
</form>
{% if res %}<div class="r {{res}}">{{titulos[res]}}<small>{{detalle}}</small></div>{% endif %}
<table><tr><th>Fecha</th><th>Referencia</th><th>Monto</th><th>Resultado</th></tr>
{% for h in hist %}<tr><td>{{h[4][:16].replace('T',' ')}}</td><td>{{h[0]}}</td><td>{{"%.2f"|format(h[1])}}</td><td>{{titulos[h[2]]}}</td></tr>{% endfor %}
</table></body></html>
"""
TITULOS = {"APROBADO": "✅ Aprobado", "NO_ENCONTRADO": "❌ No encontrado",
           "NO_ES_CREDITO": "❌ La referencia existe pero no es un pago recibido",
           "MONTO_DIFERENTE": "⚠️ Referencia encontrada, pero el monto no coincide",
           "YA_USADA": "⚠️ Esta referencia ya fue aprobada antes",
           "VARIAS": "⚠️ Varios pagos coinciden: hace falta la referencia completa",
           "ERROR": "Error"}


class Trabajador(threading.Thread):
    """Todo lo de Playwright ocurre en este hilo. Mantiene la sesión viva
    SESION_MIN minutos después de la última consulta y luego cierra sesión."""
    def __init__(self):
        super().__init__(daemon=True)
        self.cola = queue.Queue()

    def consultar(self, ref, monto):
        resp = queue.Queue()
        self.cola.put((ref, monto, resp))
        try:
            ok, valor = resp.get(timeout=90)
        except queue.Empty:
            raise RuntimeError("El banco tardó demasiado en responder. Intenta de nuevo en unos momentos.")
        if not ok:
            raise valor
        return valor

    def solicitar_cierre(self):
        resp = queue.Queue()
        self.cola.put(("__CIERRE__", 0, resp))
        try:
            return resp.get(timeout=15)
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
                    print("-> Cerrando sesion manual a peticion del usuario...")
                    b.cerrar_sesion()
                b.ultimo_uso = b.ultimo_ping = 0
                item[2].put(True)
                continue
            ref, monto, resp = item
            try:
                resp.put((True, verificar(b, ref, monto)))
            except Exception as e:
                resp.put((False, e))


def main():
    trabajador = Trabajador()
    trabajador.start()
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        res = detalle = None
        con = db()
        if request.method == "POST":
            ref = solo_digitos(request.form["referencia"])
            try:
                monto = a_numero(request.form["monto"])
                res, detalle, ref_banco = trabajador.consultar(ref, monto)
                if res == "APROBADO":
                    previo = con.execute("SELECT fecha FROM verificados WHERE resultado='APROBADO' "
                                         "AND referencia=?", (ref_banco,)).fetchone()
                    if previo:
                        res = "YA_USADA"
                        detalle = f"Ya se aprobó el {previo[0][:16].replace('T', ' ')} · {detalle}"
                    else:
                        ref = ref_banco          # se guarda la referencia completa del banco
                con.execute("INSERT INTO verificados VALUES(?,?,?,?,?)",
                            (ref, monto, res, detalle, datetime.now().isoformat()))
                con.commit()
            except Exception as e:
                res, detalle = "ERROR", str(e)
        hist = con.execute("SELECT * FROM verificados ORDER BY fecha DESC LIMIT 20").fetchall()
        return render_template_string(HTML, res=res, detalle=detalle, hist=hist,
                                      titulos=TITULOS, cuenta=CUENTA)

    @app.route("/cerrar", methods=["GET", "POST"])
    def cerrar():
        trabajador.solicitar_cierre()
        return redirect("/")

    print("\n[OK] Conciliador BDV funcionando en http://127.0.0.1:5000")
    print(f"  Sesión del banco: se abre en la primera consulta, se mantiene viva y se cierra")
    print(f"  sola tras {SESION_MIN:g} min sin consultas. Deja esta ventana abierta.")
    print("  Para apagar el programa: Ctrl+C (cierra la sesión del banco antes de salir).\n")
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    try:
        app.run(host="127.0.0.1", port=5000)
    finally:
        print("\nCerrando sesión del banco...")
        trabajador.detener()


if __name__ == "__main__":
    main()
