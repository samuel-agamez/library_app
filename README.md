# Biblioteca — app móvil (`library_app`)

App móvil de la Unidad 03 (semanas 9–12) construida con **Expo SDK 57**, **React Native**, **Expo Router**, **SQLite** y **TypeScript**.

Consume la API de [`../library_api`](../library_api), guarda datos localmente y sincroniza cuando vuelve la conexión. No usa Firebase ni guarda secretos: solo conoce la URL pública de la API.

## Requisitos

- Node.js 22.12+
- Expo Go (SDK 57) o emulador Android/iOS
- API local o desplegada

## Configuración

Copia `.env.example` a `.env`:

```env
EXPO_PUBLIC_API_URL=https://libraryapi-six.vercel.app
```

| Entorno | URL |
|---|---|
| Vercel | `https://libraryapi-six.vercel.app` |
| Teléfono + API local | `http://IP-DE-TU-PC:3000` |
| Emulador Android | `http://10.0.2.2:3000` |
| iOS/web | `http://localhost:3000` |

## Ejecutar

```bash
npm install
npx expo start
```

Atajos: `npm run android`, `npm run ios`, `npm run web`.

## Cuentas demo

| Rol | Correo | Clave |
|---|---|---|
| Estudiante | `estudiante@biblioteca.com` | `tdea2026` |
| Bibliotecario | `admin@biblioteca.com` | `tdea2026` |

## Comandos

| Comando | Qué hace |
|---|---|
| `npm start` | Servidor de desarrollo de Expo |
| `npm run android` / `ios` / `web` | Abre la app en cada plataforma |
| `npm test` | Pruebas con Jest |
| `npm run typecheck` | Revisa TypeScript |
| `npm run lint` | ESLint |

## Estructura

```text
src/app/            rutas de Expo Router
src/components/     componentes reutilizables
src/providers/      sesión y datos
src/services/       API, autenticación, sincronización y portadas
src/db/             SQLite: esquema, migraciones y repositorios
src/hooks/          hooks de datos y tema
src/types/          tipos compartidos
__tests__/          pruebas
docs/               guía completa (PDF y Markdown)
```

## Notas

- `expo export --platform web` falla por `expo-sqlite`/`wa-sqlite.wasm`; usa Android/iOS o Expo Go.
- Documentación completa en `docs/guia-app-movil.md`.
