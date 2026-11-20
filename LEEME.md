# Conciliador BDV

Escribes una referencia y un monto, y el programa revisa tu BDVenlínea y te dice si el pago llegó.

## Cómo abrirlo

- **Windows:** doble clic en `iniciar.bat`
- **Mac / Linux:** ejecuta `./iniciar.sh`

Solo necesitas tener instalado Python 3.10 o más reciente (en Windows, marca "Add Python to PATH" al instalarlo).

La primera vez que lo abras, el programa:
1. Instala lo que necesita (tarda unos minutos).
2. Abre el archivo `.env` para que pongas tu usuario y los últimos 4 dígitos de tu cuenta. La clave puedes dejarla vacía y te la pedirá al arrancar.

Después se abre solo en tu navegador, en http://127.0.0.1:5000.

## Uso

Escribe la referencia (completa o los últimos dígitos), el monto, y presiona Enter. El formulario queda listo para la siguiente consulta.

| Resultado | Significado |
|---|---|
| ✅ Aprobado | Es un crédito con esa referencia y ese monto |
| ❌ No encontrado | La referencia no está en los movimientos |
| ❌ No es un pago recibido | La referencia existe, pero es un débito |
| ⚠️ Monto no coincide | Muestra el monto que aparece en el banco |
| ⚠️ Ya usada | Ese pago ya se aprobó antes (protege contra capturas repetidas) |

**Deja la ventana negra abierta.** Mientras siga abierta, el programa atiende todas las consultas que hagas.

## Sesión del banco

- Se abre en la primera consulta.
- Se mantiene viva: cada 90 segundos el programa vuelve a abrir los movimientos.
- Si pasan 10 minutos sin consultas, cierra la sesión sola. La próxima consulta vuelve a entrar.
- Al apagar el programa (Ctrl+C o cerrando la ventana), cierra la sesión antes de salir.
- Los tiempos se cambian en el `.env`.

## Seguridad

- Tus credenciales solo viven en tu computadora. No compartas el `.env` ni la carpeta `perfil_navegador`.
- Si el banco bloquea el usuario por actividad automática, deja de usar el programa y entra por la app oficial.
