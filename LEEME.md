# Conciliador BDV

La cajera escribe una referencia y un monto, y el programa revisa BDVenlínea y le dice si el pago llegó.

El programa corre en **una sola computadora (la principal)**, que es la que entra al banco. Las cajeras se conectan desde **sus propias computadoras por la red local**, usando el navegador. No hace falta instalarles nada.

```
  Caja 1 (navegador) ─┐
  Caja 2 (navegador) ─┼── red local (router / switch / wifi) ──  Computadora principal ── internet ── BDVenlínea
  Caja 3 (navegador) ─┘                                         (Conciliador + Chrome)
```

- Las cajas **no necesitan internet**, solo estar en la misma red que la computadora principal.
- La computadora principal **sí necesita internet** para entrar al banco.
- Las consultas se atienden **una a la vez** porque hay una sola sesión del banco. Si dos cajeras consultan al mismo tiempo, la segunda espera unos segundos. Así se evitan los bloqueos de "Cliente tiene una sesión activa".

---

## 1. Instalación en la computadora principal

### Requisitos

- Windows 10/11 (también funciona en Mac/Linux).
- **Python 3.10 o más reciente**, desde https://www.python.org/downloads/. Al instalarlo, marca **"Add Python to PATH"**.
- **Google Chrome** o **Microsoft Edge** instalado.

### Pasos

1. Copia la carpeta del programa en la computadora principal, por ejemplo en `C:\ConciliadorBDV`.
2. Haz doble clic en **`iniciar.bat`**. La primera vez:
   - Instala lo que necesita (tarda unos minutos y requiere internet).
   - Abre el archivo **`.env`** en el Bloc de notas. Llena tus datos (ver la tabla de abajo), guarda y cierra.
3. En la ventana negra el programa te pide **crear el usuario administrador** (usuario y clave). Con ese usuario entras a la página y creas a las cajeras.
4. Si dejaste `BDV_CLAVE` vacía, la pide en la ventana negra.
5. Se abre el navegador en http://127.0.0.1:5000. Entra con el usuario administrador.

En Mac/Linux usa `./iniciar.sh` en lugar de `iniciar.bat`.

### Configuración (`.env`)

| Variable | Qué es | Ejemplo |
|---|---|---|
| `BDV_USUARIO` | Tu usuario de BDVenlínea | `miusuario` |
| `BDV_CLAVE` | Tu clave de BDVenlínea. Si la dejas vacía, se pide al arrancar (más seguro, pero entonces no puede arrancar solo, ver sección 4) | |
| `BDV_CUENTA` | Últimos 4 dígitos de la cuenta donde recibes los pagos | `1234` |
| `BDV_OCULTAR_NAVEGADOR` | `si` para que no se vea la ventana del banco (cuando ya confíes en que funciona) | `no` |
| `BDV_SESION_MINUTOS` | Minutos sin consultas antes de cerrar la sesión del banco | `10` |
| `BDV_PING_SEGUNDOS` | Cada cuántos segundos se "toca" el banco para que no cierre la sesión | `90` |
| `BDV_ESCUCHAR_RED` | `si` para que entren las cajeras desde otras computadoras. `no` = solo esta computadora | `si` |
| `BDV_PUERTO` | Puerto de la página | `5000` |
| `BDV_DEPURAR` | `si` para guardar captura y tabla de cada consulta en `diagnostico/` | `no` |

Después de cambiar el `.env`, cierra la ventana negra y vuelve a abrir `iniciar.bat`.

---

## 2. Crear los usuarios de las cajeras

1. Entra como administrador y abre **Usuarios** (arriba a la derecha).
2. En **Crear usuario** escribe:
   - el usuario, por ejemplo `maria` (sin espacios ni tildes);
   - el nombre;
   - una clave de mínimo 6 caracteres;
   - el rol **Cajera**.
3. Dale a cada cajera su usuario y clave. **Cada una debe tener el suyo**, así el historial muestra quién aprobó cada pago.

Qué puede hacer cada rol:

| | Cajera | Administrador |
|---|---|---|
| Verificar pagos | ✅ | ✅ |
| Ver historial | Solo el suyo | El de todas, con el nombre de la cajera |
| Crear usuarios, cambiar claves, activar/desactivar | ❌ | ✅ |
| Cerrar la sesión del banco | ❌ | ✅ |

- Si una cajera se va, **desactívala**. Los usuarios no se borran, para que el historial siga mostrando quién verificó cada pago. Si estaba conectada, queda fuera al instante.
- Si una cajera olvida su clave, el administrador le pone una nueva en la columna **Nueva clave**.
- **Si se olvida la clave del administrador:** en la computadora principal haz doble clic en **`cambiar_admin.bat`** y escribe el usuario administrador y la clave nueva.

---

## 3. Conectar las computadoras de las cajeras (red local)

Todo esto se hace **una sola vez** en la computadora principal.

### 3.1 Activar el acceso por red

En el `.env` pon:

```
BDV_ESCUCHAR_RED=si
```

Al abrir `iniciar.bat`, la ventana negra muestra la dirección para las cajeras:

```
  En esta computadora:  http://127.0.0.1:5000
  Para las cajeras:     http://192.168.1.50:5000
```

### 3.2 Darle una IP fija a la computadora principal

Si la IP cambia (por ejemplo, después de reiniciar el router), las cajeras dejan de poder entrar. Hay dos formas de fijarla. **Recomendado: reservarla en el router.**

- **Reserva en el router.** Entra a la configuración del router (normalmente http://192.168.1.1 o http://192.168.0.1; el usuario y la clave suelen estar en una etiqueta del router). Busca **"DHCP"**, **"Reserva de IP"** o **"Address Reservation"** y reserva la IP actual para la computadora principal. Se identifica por su dirección MAC, que ves con `ipconfig /all` en "Dirección física".
- **IP estática en Windows.** Ve a Configuración → Red e Internet → (Ethernet o Wi-Fi) → Editar asignación de IP → Manual. Usa una IP fuera del rango que reparte el router, por ejemplo `192.168.1.200`, con la misma puerta de enlace y DNS que tenía.

Si es posible, conecta la computadora principal al router **por cable**. Es más estable que el wifi.

### 3.3 Abrir el firewall de Windows

1. Marca la red de la computadora principal como **Privada**: Configuración → Red e Internet → Propiedades de la red → Perfil de red: **Privada**.
2. Haz clic derecho sobre **`abrir_firewall.bat`** y elige **"Ejecutar como administrador"**. Esto abre el puerto del programa solo para redes privadas.

Si prefieres hacerlo a mano, en una consola de administrador:

```
netsh advfirewall firewall add rule name="Conciliador BDV" dir=in action=allow protocol=TCP localport=5000 profile=private
```

### 3.4 En cada computadora de caja

1. Abre el navegador (Chrome, Edge o Firefox) y entra a la dirección de las cajeras, por ejemplo `http://192.168.1.50:5000`.
2. Inicia sesión con el usuario de la cajera.
3. Guarda la página en **favoritos** o crea un **acceso directo en el escritorio**: clic derecho en el escritorio → Nuevo → Acceso directo → pega la dirección.

La sesión de la cajera dura **12 horas** (un turno). Después pide usuario y clave otra vez.

### 3.5 Probar la conexión

Si una caja no puede entrar:

1. Confirma que la ventana negra del programa está abierta en la computadora principal.
2. Desde la caja abre una consola (`cmd`) y ejecuta `ping 192.168.1.50` (con la IP de la principal). Si no responde, puede que no estén en la misma red, o que el firewall de Windows bloquee el ping (lo hace por defecto en algunos equipos). En ese caso prueba directamente la página.
3. Si el ping responde pero la página no abre, revisa el firewall (paso 3.3) y que la red esté como **Privada**.
4. Revisa que `BDV_ESCUCHAR_RED=si` esté en el `.env` y que hayas reiniciado el programa.

---

## 4. Dejar la computadora principal lista para el día a día

- **Que no se suspenda:** Configuración → Sistema → Inicio/apagado y suspensión → "Suspender" en **Nunca** (con el equipo enchufado). Si se suspende, las cajeras no pueden consultar.
- **Que el programa arranque solo al encender:**
  1. Pulsa `Win + R`, escribe `shell:startup` y presiona Enter.
  2. En esa carpeta crea un acceso directo a `iniciar.bat`.
  3. Para que arranque sin que nadie escriba nada, **`BDV_CLAVE` debe estar en el `.env`**. Si no, se queda esperando la clave en la ventana negra.
- **Deja la ventana negra abierta.** Mientras siga abierta, el programa atiende a todas las cajeras. Puedes minimizarla.

---

## 5. Uso (cajeras)

Escribe la referencia (completa, o **al menos los últimos 6 dígitos**) y presiona Enter. El formulario queda listo para la siguiente consulta.

- **Con monto** (`2000,00`, `2.000,00` o `2.000`): comprueba que la referencia y el monto coincidan.
- **Sin monto** (deja la casilla vacía): busca solo la referencia y te dice **cuánto se recibió**. Compara tú ese monto con lo que te deben.

| Resultado | Significado |
|---|---|
| ✅ Aprobado | Hay un crédito con esa referencia (y ese monto, si lo escribiste). Muestra el monto que aparece en el banco |
| ❌ No encontrado | La referencia no está en los movimientos |
| ❌ No es un pago recibido | La referencia existe, pero es un débito |
| ⚠️ Monto no coincide | Muestra el monto que aparece en el banco |
| ⚠️ Ya usada | Ese pago ya se aprobó antes, y muestra cuándo y qué cajera lo aprobó (protege contra capturas repetidas) |
| ⚠️ Varios pagos coinciden | Hay más de un crédito con esos dígitos: escribe la referencia completa (o el monto) |

La referencia tiene que coincidir con el **final** de la referencia del banco. "123456" encuentra "000123456", pero no "991234567". Si la captura trae más dígitos que los que muestra el banco, también la encuentra.

### Si dice "No encontrado" y el pago sí está

Cada vez que el resultado es "No encontrado", el programa guarda en la carpeta **`diagnostico/`** una captura de la pantalla del banco y un archivo `.json` con lo que leyó de la tabla. Si pasa con un pago que sí está, revisa esos archivos o envíaselos a quien te da soporte. **Contienen tus movimientos: no los publiques.**

Para guardar el diagnóstico en todas las consultas, pon `BDV_DEPURAR=si` en el `.env`.

---

## 6. Sesión del banco

- Se abre en la primera consulta del día (de cualquier cajera).
- Se mantiene viva: cada 90 segundos el programa vuelve a abrir los movimientos.
- Si pasan 10 minutos sin consultas, se cierra sola. La próxima consulta vuelve a entrar.
- El administrador puede cerrarla cuando quiera con **Cerrar sesión BDV**.
- Al apagar el programa (Ctrl+C o cerrando la ventana negra), se cierra la sesión antes de salir.
- Los tiempos se cambian en el `.env`.
- Mientras el programa está conectado, **no entres a BDVenlínea desde el teléfono con el mismo usuario**: el banco solo permite una sesión a la vez.

---

## 7. Seguridad

- Las credenciales del banco solo viven en la computadora principal. No compartas el `.env`, la carpeta `perfil_navegador`, el archivo `.secreto_web` ni `historial.db`.
- Las claves de las cajeras se guardan cifradas (hash), nunca en texto.
- Tras 5 intentos fallidos de entrar desde una misma computadora, esa computadora queda bloqueada 5 minutos.
- La página viaja **sin cifrar dentro de la red local**. Si tienes wifi para clientes, **sepáralo de la red de las cajas**: usa la red de invitados del router o una red distinta. Así nadie de afuera puede ver la página ni intentar entrar.
- Si el banco bloquea el usuario por actividad automática, deja de usar el programa y entra por la app oficial.

---

## Archivos

| Archivo | Para qué |
|---|---|
| `iniciar.bat` / `iniciar.sh` | Abre el programa (y lo instala o actualiza si hace falta) |
| `abrir_firewall.bat` | Abre el puerto en el firewall de Windows (una vez, como administrador) |
| `cambiar_admin.bat` | Crea un administrador o le cambia la clave |
| `.env` | Tu configuración (se crea la primera vez) |
| `historial.db` | Historial de verificaciones y usuarios |
| `app.py`, `templates/` | El programa |
