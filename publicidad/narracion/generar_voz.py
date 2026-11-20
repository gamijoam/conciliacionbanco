"""Genera la voz del video con Piper (voz neuronal, funciona sin internet).

Uso (desde la carpeta publicidad):
    pip install piper-tts
    python narracion/generar_voz.py

Descarga la voz la primera vez (~60 MB), crea public/voz/<id>.wav y escribe
src/voz.json con en qué frame empieza cada frase y cuánto dura cada escena.
Después: npm run video
"""
import json
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SALIDA = RAIZ / "public" / "voz"
MODELOS = AQUI / "modelos"


def descargar_voz(nombre):
    """es_MX-claude-high -> https://huggingface.co/rhasspy/piper-voices/.../es/es_MX/claude/high/..."""
    MODELOS.mkdir(exist_ok=True)
    idioma, hablante, calidad = nombre.split("-")
    base = (f"https://huggingface.co/rhasspy/piper-voices/resolve/main/"
            f"{idioma.split('_')[0]}/{idioma}/{hablante}/{calidad}/{nombre}")
    for ext in (".onnx", ".onnx.json"):
        destino = MODELOS / f"{nombre}{ext}"
        if not destino.exists():
            print(f"Descargando {destino.name}...")
            urllib.request.urlretrieve(base + ext, destino)
    return MODELOS / f"{nombre}.onnx"


def duracion_seg(ruta):
    with wave.open(str(ruta)) as w:
        return w.getnframes() / w.getframerate()


def main():
    guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
    modelo = descargar_voz(guion["voz"])
    fps = guion["fps"]
    SALIDA.mkdir(parents=True, exist_ok=True)
    resultado = {"fps": fps, "escenas": {}}
    total = 0
    for escena, datos in guion["escenas"].items():
        fin_anterior = 0
        frases = []
        for f in datos["frases"]:
            wav = SALIDA / f"{f['id']}.wav"
            subprocess.run([sys.executable, "-m", "piper", "-m", str(modelo), "-f", str(wav),
                            "--length-scale", str(guion["velocidad"]), "--sentence-silence", "0.15"],
                           input=f["texto"].encode("utf-8"), check=True, capture_output=True)
            dur = round(duracion_seg(wav) * fps)
            desde = max(f.get("min", 0), fin_anterior + f.get("pausa", 8))
            frases.append({"id": f["id"], "desde": desde, "frames": dur})
            fin_anterior = desde + dur
            print(f"  {f['id']:<12} empieza en {desde:>4}  dura {dur:>4} frames  ({f['texto'][:50]})")
        duracion = max(datos["base"], fin_anterior + guion["cola"])
        resultado["escenas"][escena] = {"duracion": duracion, "frases": frases}
        total += duracion
        print(f"{escena}: {duracion} frames")
    (RAIZ / "src" / "voz.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    print(f"\nListo: video de {total / fps:.1f} s. Ahora ejecuta: npm run video")


if __name__ == "__main__":
    main()
