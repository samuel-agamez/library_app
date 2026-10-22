# Biblioteca — app móvil (`library_app`)

App de la Unidad 03 *Integración con API, seguridad y servicios del dispositivo* (semanas 9 a 12), construida con **Expo SDK 57**, **React Native 0.86**, **Expo Router**, **expo-sqlite**, **expo-secure-store**, **NetInfo** y **expo-image-picker**.

Consume únicamente la API REST de [`../library_api`](../library_api). **No habla con Firebase ni guarda secretos**: en el bundle solo existe la URL pública de la API (`EXPO_PUBLIC_API_URL`).

## Qué incluye

| Semana | Contenido |
|---|---|
| 9 | Consumo de API REST: cliente HTTP con timeout, manejo uniforme de errores, configuración por ambiente |
| 10 | Login/registro, tokens en **SecureStore**, roles (estudiante/bibliotecario), refresco automático ante 401 |
| 11 | **SQLite**: caché del catálogo, préstamos locales, cola *outbox* y sincronización al recuperar la red |
| 12 | Servicio del dispositivo: **cámara/galería** para portadas, optimización de imagen y subida a la API |

Funciona sin conexión: lee de SQLite, encola solicitudes y las envía cuando vuelve la red. El servidor siempre es la fuente de verdad.

## Requisitos

- **Node.js 22.12 o superior** (probado con 24.19.0).
- **Expo Go** (SDK 57) en el teléfono, o un emulador Android/iOS.
- La API corriendo: en local (`../library_api`) o la desplegada del curso.

## Configurar la URL de la API

Copia `.env.example` a `.env` (ya viene creado apuntando a la API del curso):

```env
EXPO_PUBLIC_API_URL=https://library-api-beige-seven.vercel.app
```

| Dónde corre la app | Valor |
|---|---|
| API desplegada | `https://library-api-beige-seven.vercel.app` |
| Teléfono físico con API local | `http://IP-DE-TU-PC:3000` (misma red Wi-Fi y `npm run dev:lan` en la API) |
| Emulador Android | `http://10.0.2.2:3000` |
| Simulador iOS / web | `http://localhost:3000` |

> Todo lo que empieza por `EXPO_PUBLIC_` es visible en la app: nunca pongas claves de Firebase aquí.

## Instalar y ejecutar

```bash
npm install
npx expo start          # escanea el QR con Expo Go
```

Atajos: `npm run android`, `npm run ios`, `npm run web`.

## Cuentas de prueba

Con la API del curso:

| Rol | Usuario | Clave |
|---|---|---|
| Estudiante | `estudiante@gmail.com` | `tdea2026` |
| Bibliotecario | `admin@gmail.com` | `tdea2026` |

También puedes crear tus propias cuentas en la API (`npm run create-user`). En tu propia API no hay usuarios escritos en el código.

## Comandos

| Comando | Qué hace |
|---|---|
| `npm start` | Servidor de desarrollo de Expo |
| `npm run android` / `ios` / `web` | Abre la app en cada plataforma |
| `npm test` | Pruebas (Jest): 66 aprobadas |
| `npm run typecheck` | TypeScript sin emitir |
| `npm run lint` | ESLint (expo lint) |

## Prueba de integración real (opcional)

Con la API encendida y cuentas propias:

```bash
E2E_API_URL=http://localhost:3000 \
E2E_STUDENT_EMAIL=... E2E_STUDENT_PASSWORD=... \
E2E_LIBRARIAN_EMAIL=... E2E_LIBRARIAN_PASSWORD=... \
npx jest e2e-api
```

Verifica login, sincronización del catálogo, solicitud “sin conexión”, push de la cola, aprobación/devolución por el bibliotecario, 403 de estudiante y refresco de token.

> La prueba asume una cuenta de estudiante **sin préstamos previos** (`toHaveLength(1)`). Con la cuenta demo compartida puede fallar por datos acumulados aunque la app funcione.

## Estructura

```text
src/app/            rutas (Expo Router): sign-in, sign-up, tabs, book/[id]
src/components/     UI reutilizable (botón, campos, tarjetas, estados)
src/providers/      AuthProvider y DataProvider (sesión + datos)
src/services/api/   cliente HTTP (timeout, errores, refresh)
src/services/auth/  login/registro y SessionManager (SecureStore)
src/services/sync/  sincronización catálogo/outbox
src/services/loans/ reglas locales de préstamo
src/services/device/portadas (image picker + manipulación)
src/db/             esquema, migraciones y repositorios SQLite
src/hooks/          use-library-data, tema, color scheme
src/types/          tipos compartidos
__tests__/          pruebas unitarias, de flujo offline y E2E
docs/               guía completa (Markdown y PDF)
```

## Verificación

```bash
npm test        # 66 pruebas aprobadas (3 omitidas)
npm run typecheck
npm run lint
npx expo export --platform android   # bundle de producción
```

> `expo export --platform web` no funciona con esta combinación de `expo-sqlite` (Metro no resuelve `wa-sqlite.wasm`). El objetivo de la unidad es Android/iOS; usa el emulador o Expo Go.

## Documentación de la unidad

- `docs/Guia_App_Movil_Biblioteca.pdf` — Guía 2 (app móvil), semanas 9 a 12.
- `docs/guia-app-movil.md` — la misma guía en Markdown, con el código completo.
- Guía 1 (API y web): [`../library_api/docs/Guia_API_Web_Biblioteca.pdf`](../library_api/docs/Guia_API_Web_Biblioteca.pdf).
