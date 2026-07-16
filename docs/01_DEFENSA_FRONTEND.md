# 01 · Defensa del Rol Frontend

## 1. Nombre del rol
**Integrante A — Frontend Engineer.** Rama `feature/frontend`.

## 2. Archivos bajo mi responsabilidad
- `frontend/index.html` — estructura de la interfaz.
- `frontend/styles.css` — estilos responsivos.
- `frontend/app.js` — lógica, llamadas a la API y renderizado seguro.

## 3. Objetivo de mi capa
Ofrecer una interfaz clara, accesible y responsiva para registrar, listar, editar y eliminar visitantes, consumiendo la API mediante **rutas relativas** y **Fetch API**, sin recargar la página completa.

## 4. Explicación detallada (fácil de memorizar)
- El HTML define un **formulario** (nombre, correo, categoría) y una **tabla** dinámica.
- El JavaScript escucha el evento `submit`, arma un objeto JSON y lo envía con `fetch`.
- Según si hay un `id` oculto en el formulario, decide entre **POST** (crear) o **PUT** (editar).
- Al recibir la respuesta, muestra un mensaje y **vuelve a pedir la lista** para refrescar solo la tabla.
- La tabla se construye con `document.createElement` y `textContent`, nunca con `innerHTML` de datos del usuario → **previene XSS**.

## 5. Flujo de una petición a través de mi capa
1. El usuario envía el formulario.
2. `guardarVisitante()` valida que los campos no estén vacíos.
3. `fetch("/api/visitantes", {method:"POST"|"PUT"})` con `Content-Type: application/json`.
4. Se interpreta el código HTTP: 201/200 → éxito; 400/409 → mensaje de error de la API.
5. `cargarVisitantes()` recarga la tabla con `GET /api/visitantes`.

## 6. Fragmentos de código importantes

Ruta relativa y envío:
```javascript
const API_BASE = "/api/visitantes";
const resp = await fetch(url, {
  method: editando ? "PUT" : "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
```

Renderizado seguro (anti-XSS):
```javascript
function crearCelda(texto) {
  const td = document.createElement("td");
  td.textContent = texto == null ? "" : String(texto);
  return td;
}
```

## 7. Comandos que debo conocer
```bash
docker compose up -d --build      # levantar todo
docker compose logs nginx         # ver logs del servidor que sirve el frontend
```
En el navegador: **F12 → Network** para ver las peticiones `fetch` y sus códigos.

## 8. Salidas esperadas
- Al registrar: mensaje verde "Visitante registrado correctamente." y la tabla actualizada.
- Al buscar: la tabla se filtra tras ~350 ms (debounce).
- Sin datos: mensaje "No hay visitantes registrados todavía."

## 9. Fallos comunes
- La tabla no carga → la API responde error (revisar Network).
- Mensaje "Error de red" → Nginx o backend caídos.
- Nada ocurre al enviar → campo obligatorio vacío (validación del cliente).

## 10. Cómo diagnosticar fallos
- Abrir **DevTools → Network**, revisar la petición `/api/visitantes` y su código HTTP.
- Revisar **Console** por errores de JavaScript.
- Comprobar que la URL es **relativa** (`/api/...`) y no una IP fija.

## 11. Cómo recuperarme
- Recargar la página (Ctrl+F5) para descartar caché.
- Pulsar **Actualizar** para reintentar el `GET`.
- Si la API falla, avisar al Backend/DevOps; el frontend ya muestra el error de forma controlada.

## 12. Consideraciones de seguridad
- **XSS prevenido** usando `textContent` y `createElement`, nunca `innerHTML` con datos del usuario.
- No se guardan credenciales en el navegador.
- Mismo origen → sin exposición de tokens ni CORS.

## 13. Consideraciones de rendimiento
- Búsqueda con **debounce** (350 ms) para no saturar la API.
- Se refresca **solo la tabla**, no toda la página.
- Construcción de filas con `DocumentFragment` para minimizar reflows.

## 14. Diez preguntas probables del profesor
1. ¿Por qué usas rutas relativas y no la IP del servidor?
2. ¿Cómo evitas ataques XSS al mostrar los datos?
3. ¿Qué diferencia hay entre POST y PUT en tu código?
4. ¿Cómo refrescas la tabla sin recargar la página?
5. ¿Qué es la Fetch API y por qué usas `async/await`?
6. ¿Cómo manejas los errores que devuelve la API?
7. ¿Cómo haces la interfaz responsiva?
8. ¿Qué es el debounce en la búsqueda?
9. ¿Cómo validas los datos antes de enviarlos?
10. ¿Por qué el frontend no necesita configuración de CORS?

## 15. Diez respuestas modelo
1. Porque el frontend y la API comparten origen a través de Nginx; una ruta relativa funciona en local, en EC2 o con cualquier IP sin cambiar el código, y evita hardcodear direcciones.
2. Uso `textContent` y `document.createElement` en lugar de `innerHTML`; así cualquier `<script>` en un nombre se muestra como texto y no se ejecuta.
3. Si el formulario tiene un `id` oculto, envío **PUT** a `/api/visitantes/<id>` (actualizar); si no, envío **POST** a `/api/visitantes` (crear).
4. Tras una operación exitosa llamo a `cargarVisitantes()`, que hace un `GET` y reconstruye solo el `<tbody>` con `replaceChildren`.
5. Es la API nativa del navegador para peticiones HTTP; `async/await` hace el código legible y me permite esperar la respuesta y su `.json()`.
6. Leo `resp.status`; si no es 200/201/204 intento leer `data.error` del cuerpo JSON y lo muestro en un mensaje rojo.
7. Con CSS: un contenedor de ancho máximo centrado, `flex-wrap` en los botones, `overflow-x` en la tabla y un `@media (max-width:600px)`.
8. Es un temporizador que espera 350 ms tras la última tecla antes de buscar, evitando una petición por cada carácter.
9. Antes de enviar compruebo que nombre, correo y categoría no estén vacíos; el backend hace la validación definitiva.
10. Porque no hay petición entre orígenes distintos: el navegador pide a `http://servidor/` y la API está en el mismo `http://servidor/api/`.

## 16. Guion de defensa oral (2 minutos)
"Soy el responsable del frontend. Construí la interfaz con HTML, CSS y JavaScript puro. El usuario registra visitantes con nombre, correo y categoría, y ve la lista en una tabla dinámica. Todas las llamadas usan Fetch API con **rutas relativas** como `/api/visitantes`, así que el mismo código funciona en local y en AWS sin cambiar ninguna IP. Distingo entre crear (POST) y editar (PUT) según un id oculto en el formulario, y tras cada operación refresco solo la tabla, sin recargar la página. Para seguridad, renderizo los datos con `textContent` y `createElement`, nunca con `innerHTML`, lo que previene ataques XSS. Muestro mensajes de éxito y error, un estado vacío, un indicador de carga y una búsqueda con debounce. La interfaz es responsiva y accesible con etiquetas y foco de teclado."

## 17. Guion de defensa oral extendido (5 minutos)
Añade al guion de 2 minutos:
- **Arquitectura**: "El navegador solo habla con Nginx en el puerto 80. Nginx sirve mis archivos estáticos y reenvía `/api/` al backend. Por eso comparto origen con la API y no necesito CORS."
- **Flujo detallado**: describe `submit → validación → fetch → interpretación del código HTTP → refresco de tabla`.
- **Manejo de errores**: "Si la API devuelve 409 por correo duplicado, leo `data.error` y lo muestro en rojo; el usuario entiende qué pasó."
- **Rendimiento**: "Uso debounce en la búsqueda y `DocumentFragment` para insertar filas de una sola vez."
- **Accesibilidad**: "Cada campo tiene su `<label>`, uso `aria-live` para los mensajes y la confirmación antes de borrar."
- Cierra relacionando tu capa con las otras tres (ver sección 20).

## 18. Checklist de demostración en vivo
- [ ] Abrir `http://localhost` y mostrar la interfaz.
- [ ] Registrar un visitante y mostrar el mensaje de éxito.
- [ ] Mostrar la fila nueva en la tabla.
- [ ] Editar ese visitante (cambiar categoría) y guardar.
- [ ] Buscar por nombre/correo.
- [ ] Eliminar con confirmación.
- [ ] Abrir DevTools → Network y mostrar que las URLs son relativas `/api/...`.

## 19. Lo que NUNCA debo decir mal
- **NO** digo que uso React/Vue/Angular: es **JavaScript puro**.
- **NO** digo que el frontend se conecta "directo a la base de datos": pasa por la API.
- **NO** digo que uso `fetch("http://IP:5000/...")`: son rutas **relativas**.
- **NO** digo que uso `innerHTML` con datos del usuario: uso `textContent`.

## 20. Relación con las otras tres capas
- **Backend**: consumo su API REST y respeto sus códigos HTTP (201, 400, 404, 409).
- **Base de datos**: nunca la toco directamente; el backend es el intermediario.
- **DevOps/Nginx**: Nginx sirve mis archivos y me da el mismo origen que la API, permitiéndome usar rutas relativas sin CORS.
