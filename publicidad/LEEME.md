# Publicidad del Conciliador

Video e imágenes para Facebook e Instagram, hechos con [Remotion](https://www.remotion.dev/) (video programado con React).

## Piezas

| Archivo | Tamaño | Dónde usarlo |
|---|---|---|
| `salida/Video-Reels.mp4` | 1080×1920, 48 s, con voz | Reels, Stories y anuncios verticales |
| `salida/Post-Aprobado.png` | 1080×1350 (4:5) | Feed: "¿Te llegó el pago? Compruébalo en segundos" |
| `salida/Post-Fraude.png` | 1080×1350 (4:5) | Feed: capturas repetidas |
| `salida/Post-AntesAhora.png` | 1080×1350 (4:5) | Feed: antes y ahora |
| `salida/Historia.png` | 1080×1920 | Historias |

Guion del video:

1. Gancho: "¿Te llegó el pago móvil?", con la captura del cliente.
2. El problema: abrir el banco, usuario, clave y código, buscar entre cientos de movimientos… con cada pago.
3. Aparece la marca.
4. Demo: referencia + monto → ✅ Aprobado.
5. Fraude: la misma captura otra vez → ⚠️ ya fue usada.
6. Beneficios.
7. Llamado a la acción: WhatsApp.

El video tiene **voz en español latino neutro** (acento mexicano), pero no tiene música, para no tener problemas de derechos. Agrega la música desde el editor de Instagram o Facebook al publicar, con su biblioteca de música libre y a volumen bajo para que no tape la voz.

## Voz

La genera [Piper](https://github.com/OHF-Voice/piper1-gpl), una voz neuronal que funciona sin internet y sin pagar. Se usa la voz `es_MX-claude-high`, de licencia Apache-2.0, que permite uso comercial.

- El texto está en **`narracion/guion.json`**. Cada frase tiene su escena y su momento.
- Los audios ya generados están en `public/voz/`. Con ellos, `npm run video` funciona sin instalar Piper.
- Para cambiar el texto o la velocidad (`velocidad`: más bajo = más rápido):

  ```bash
  pip install piper-tts
  python narracion/generar_voz.py   # crea los audios y src/voz.json
  npm run video
  ```

  El video ajusta solo la duración de cada escena y el momento de cada animación según lo que dure la voz.
- Algunas palabras cortas sueltas suenan poco claras con esta voz (por ejemplo "pago" al final de una frase). Escucha el resultado y, si algo no se entiende, cambia la frase.
- Los números se dictan como se dicen en Venezuela: "cero cuatro dos dos, setecientos cuarenta y uno, cero cero, noventa y cuatro".

## Cambiar nombre, WhatsApp o colores

Todo está en **`src/config.ts`**: `MARCA`, `ESLOGAN`, `WHATSAPP`, `AVISO_LEGAL` y los colores. Cambia ahí y vuelve a generar.

## Generar de nuevo

Necesitas Node.js 18 o más reciente.

```bash
cd publicidad
npm install          # solo la primera vez
npm run estudio      # abre un editor en el navegador para ver y ajustar el video
npm run imagenes     # genera los PNG en salida/
npm run video        # genera el MP4 en salida/
```

## Recomendaciones para publicar

- **Público:** Venezuela, de 25 a 55 años. Intereses: emprendimiento, pequeñas empresas, comercio, ventas por Instagram.
- **Texto sugerido para la publicación:**
  > ¿Cansado de entrar al banco cada vez que un cliente te dice "ya te pagué"? 🏦
  > Con Conciliador escribes la referencia y el monto, y en segundos sabes si el pago móvil llegó de verdad. Además te avisa si te mandan la misma captura dos veces. ✅
  > Escríbenos por WhatsApp 👉 0422-7410094
- **No uses el logo ni los colores del Banco de Venezuela.** Mantén el aviso "Producto independiente. No está afiliado al Banco de Venezuela."
- **No prometas cosas que dependen del banco** (por ejemplo "nunca más tendrás que entrar"): el programa usa tu sesión de BDVenlínea y puede verse afectado si el banco cambia su página.
