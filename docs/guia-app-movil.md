---
title: Construye la app móvil de la Biblioteca
subtitle: Tutorial paso a paso con React Native, Expo y SQLite. Unidad 03: semanas 9 a 12
kicker: Desarrollo Móvil · Ingeniería en Software · Guía 2 de 2: construye esta después de la API
header: Guía 2 · App móvil
facts: Asignatura=Desarrollo Móvil (PREISESP17015);;Unidad=03 · Integración con API, seguridad y servicios del dispositivo;;Qué construirás=Una app Expo que consume la API, guarda la sesión de forma segura y funciona sin conexión con SQLite;;Requisito=La Guía 1 terminada: la API y Firebase funcionando (`pnpm smoke` en verde);;Tecnologías=Expo SDK 57, React Native 0.86, TypeScript, Expo Router, expo-sqlite, expo-secure-store, NetInfo, expo-image-picker, Jest;;Resultado=Proyecto `library_app` completo, con pruebas, listo para el hito 3
---

# 1. Antes de empezar

## 1.1 Qué vas a construir

**Biblioteca** es una app móvil para consultar el catálogo de una biblioteca y gestionar préstamos, con dos roles y sin límite de usuarios:

| Rol | Qué puede hacer |
|---|---|
| **Estudiante** | Crear su cuenta, listar y buscar libros, ver el detalle y **solicitar el préstamo**. Ve el estado de sus solicitudes. |
| **Bibliotecario** | Ver todas las solicitudes, **prestar**, rechazar o registrar la devolución, y cambiar la portada de un libro con la cámara. |

Hasta ahora tu app hablaba **directamente con Firebase**. En esta guía la conviertes en una app que habla solo con **tu API** (Guía 1) y que **sigue funcionando sin internet**:

{{diagram:architecture}}

Tres decisiones explican casi todo el código:

- **La app nunca habla con Firebase.** Solo conoce la API REST; así las credenciales de administrador y las reglas de negocio viven en un único lugar.
- **La interfaz siempre lee de SQLite.** La red solo sirve para *sincronizar*. Por eso la app es rápida y funciona en el metro o en un ascensor.
- **El servidor es la fuente de verdad.** Si lo que hizo el teléfono sin conexión choca con el servidor, gana el servidor y se le explica al usuario.

## 1.2 Cómo usar esta guía

Es un **tutorial de construcción**: al terminarlo tienes el proyecto completo y funcionando. Cada paso tiene una etiqueta de color:

| Etiqueta | Qué debes hacer |
|---|---|
| **CREAR** | Crea el archivo en esa ruta (relativa a la raíz del proyecto) con **exactamente** ese contenido. Si ya existe, reemplázalo completo. |
| **AGREGAR A** | Agrega ese fragmento JSON a un archivo que ya existe (sin borrar lo demás). |
| **ELIMINAR** | Borra ese archivo. |
| **TERMINAL** | Ejecuta esos comandos dentro de la carpeta del proyecto. |

Algunos archivos aparecen **dos veces** (por ejemplo, `src/app/_layout.tsx`): la primera es una versión *provisional* que sirve para la semana en curso y la segunda la reemplaza por la versión definitiva. Es a propósito: así cada semana termina con una app que compila y se puede probar.

Después de cada semana hay un **punto de control**: ejecuta `npm run typecheck`, `npx expo lint` y `npm test`. Si pasan, sigues; si no, revisa el último archivo que creaste.

> [!IDEA] Trabaja con Git y haz un *commit* al terminar cada semana (`git add -A && git commit -m "semana 9"`). Si algo se rompe, `git diff` muestra qué cambió.

> [!NOTA] Los comentarios dentro del código están en español y explican el *porqué* de cada decisión. Léelos: son parte de la guía.

## 1.3 Requisitos

- **La Guía 1 terminada**: la API de `library_api` corriendo, con `pnpm seed` ejecutado y **al menos un estudiante y un bibliotecario creados** con `pnpm create-user` (Guía 1, sección 4.4). Compruébalo con `curl http://localhost:3000/api/health`.
- **Node.js 24 LTS** (mínimo 22.5), npm, Git y Visual Studio Code.
- La app **Expo Go** en tu teléfono (Android o iOS), en la misma red Wi-Fi que tu computador.

## 1.4 La URL de la API según dónde corras la app

| Dónde corre la app | Valor de `EXPO_PUBLIC_API_URL` |
|---|---|
| Teléfono físico con Expo Go | `http://IP-DE-TU-PC:3000` (ej. `http://192.168.1.20:3000`) |
| Emulador de Android | `http://10.0.2.2:3000` |
| Simulador de iOS | `http://localhost:3000` |

> [!OJO] En un teléfono físico **`localhost` es el propio teléfono**, no tu computador. Es el error de conexión más común. Además, arranca la API con `pnpm dev:lan` para que acepte conexiones de la red.

> [!OJO] Si usas **WSL2**, el puerto 3000 de WSL no es visible desde la red del teléfono por defecto. Opciones: activar `networkingMode=mirrored` en `%UserProfile%\.wslconfig`, o crear un reenvío de puertos en PowerShell de administrador: `netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=IP-DE-WSL` y permitir el puerto 3000 en el firewall de Windows.

## 1.5 Ruta de trabajo

| Semana | Guía 1 (API y web) | Esta guía (app móvil) | Lo que ya funciona al terminar |
|---|---|---|---|
| 9 | Capítulo 3: REST, validación, catálogo | Capítulo 3: cliente HTTP y estados de pantalla | La app lista libros desde la API |
| 10 | Capítulo 4: Firebase Auth, roles | Capítulo 4: sesión segura y rutas protegidas | Registro, login y roles |
| 11 | Capítulo 5: préstamos, idempotencia | Capítulo 5: SQLite offline y sincronización | Solicitudes sin conexión |
| 12 | Capítulo 6: portadas | Capítulo 6: cámara y galería | **Hito 3** |
| — | Capítulo 8: pruebas finales | Capítulo 7: pruebas de integración | Entrega |

# 2. Paso 0 · Preparar tu app

## 2.1 Punto de partida

La guía parte de un proyecto **Expo con Expo Router y TypeScript** (carpeta `src/app`), como el que crea `npx create-expo-app@latest` con la plantilla por defecto del SDK 57. Si tu app actual tiene otra estructura, crea un proyecto limpio con ese comando y trabaja allí; después podrás migrar lo que quieras conservar.

> [!OJO] Antes de empezar, **protege tu trabajo actual**: crea una rama (`git checkout -b biblioteca-api`). Esta guía reemplaza las pantallas de la plantilla (`index`, `explore`…) y la configuración de rutas. Si tienes pantallas propias que quieras conservar, muévelas a otra carpeta.

## 2.2 Retira el acceso directo a Firebase

Tu app actual usa el SDK de Firebase en el cliente. Con esta arquitectura **ya no debe hacerlo**: todo pasa por la API. Cuando termines la semana 10, haz esto en tu app original (si la conservas):

- Elimina la configuración e inicialización de Firebase (`firebaseConfig`, `initializeApp`) y los *imports* de `firebase/auth` y `firebase/firestore`.
- Reemplaza cada llamada de autenticación por las funciones de `src/services/auth/auth-service.ts` (semana 10) y cada lectura de Firestore por los hooks de `src/hooks/use-library-data.ts` (semana 11).
- Desinstala el paquete: `npm uninstall firebase`.

> [!IDEA] La razón: una app móvil se puede descomprimir; cualquier clave o regla de negocio que viva en ella es pública y modificable. Con la API, las claves de administrador nunca salen del servidor y las reglas (ejemplares, roles, conflictos) no se pueden saltar.

## 2.3 Instalar los módulos que usaremos

Instala **siempre** con `npx expo install` (no con `npm install`): Expo elige la versión compatible con tu SDK.

{{run:app}}
```bash
npx expo install expo-sqlite expo-secure-store @react-native-community/netinfo
npx expo install expo-image-picker expo-image-manipulator expo-crypto
npx expo install jest-expo jest @types/jest --dev
npx expo install @testing-library/react-native --dev
npx expo install eslint eslint-config-expo --dev
```

| Módulo | Para qué |
|---|---|
| `expo-sqlite` | Base de datos SQLite local (caché y cola offline) |
| `expo-secure-store` | Guardar los tokens de sesión en el Keychain / Keystore |
| `@react-native-community/netinfo` | Detectar si hay conexión |
| `expo-image-picker` · `expo-image-manipulator` | Cámara/galería y reducción de imágenes |
| `expo-crypto` | Generar identificadores únicos (UUID) |
| `jest-expo`, `jest`, `@testing-library/react-native` | Pruebas automáticas |
| `eslint`, `eslint-config-expo` | Reglas de calidad de código |

> [!NOTA] En Windows, si tu terminal no acepta `--dev`, escríbelo como `"--" --dev` (con las comillas), según la documentación de Expo.

## 2.4 Eliminar los archivos de ejemplo de la plantilla

La plantilla trae pantallas y componentes de ejemplo que no usaremos. Elimínalos (si tu proyecto no tiene alguno, sigue adelante):

{{delete:app:src/app/explore.tsx}}

{{delete:app:src/app/index.tsx}}

{{delete:app:src/components/animated-icon.module.css}}

{{delete:app:src/components/animated-icon.tsx}}

{{delete:app:src/components/animated-icon.web.tsx}}

{{delete:app:src/components/app-tabs.tsx}}

{{delete:app:src/components/app-tabs.web.tsx}}

{{delete:app:src/components/external-link.tsx}}

{{delete:app:src/components/hint-row.tsx}}

{{delete:app:src/components/web-badge.tsx}}

{{delete:app:src/components/ui/collapsible.tsx}}

{{delete:app:src/components/themed-view.tsx}}

{{delete:app:src/global.css}}

{{delete:app:src/hooks/use-color-scheme.web.ts}}

> [!NOTA] Esta app es **solo móvil** (Android e iOS): por eso también eliminamos los archivos `.web` y los estilos web de la plantilla. `expo-sqlite` no se usa en web.

## 2.5 Configuración del proyecto

**`app.json`.** Pon el nombre de tu app e identificadores únicos (reemplaza `estudiante` por tu usuario). Se usan al compilar el instalable en la semana 15:

{{merge:app:app.json}}
```json
{
  "expo": {
    "name": "Biblioteca",
    "android": { "package": "com.estudiante.biblioteca" },
    "ios": { "bundleIdentifier": "com.estudiante.biblioteca" }
  }
}
```

**`package.json`.** Agrega los scripts y la configuración de Jest (el alias `@/` debe resolverse también en las pruebas):

{{merge:app:package.json}}
```json
{
  "scripts": {
    "test": "jest",
    "typecheck": "tsc --noEmit"
  },
  "jest": {
    "preset": "jest-expo",
    "moduleNameMapper": {
      "^@/assets/(.*)$": "<rootDir>/assets/$1",
      "^@/(.*)$": "<rootDir>/src/$1"
    },
    "testPathIgnorePatterns": ["/node_modules/", "/.expo/"]
  }
}
```

**`tsconfig.json`.** Agrega los tipos de Jest y de Node (las pruebas usan `node:sqlite`):

{{merge:app:tsconfig.json}}
```json
{
  "compilerOptions": {
    "types": ["jest", "node"]
  }
}
```

**ESLint.** Crea la configuración (la misma que genera `npx expo lint`):

{{create:app:eslint.config.js}}

**Variables de entorno.** Crea la plantilla `.env.example` y cópiala a `.env` con la URL de tu API (ver 1.4):

{{create:app:.env.example}}

```bash
cp .env.example .env        # en PowerShell: Copy-Item .env.example .env
```

## 2.6 Base de interfaz: tema, texto, pantalla y botón

Estos cinco archivos son la base visual de todas las pantallas. No tienen lógica de negocio, pero todo lo demás depende de ellos.

El **tema** define colores claros y oscuros, espaciado y medidas:

{{create:app:src/constants/theme.ts}}

Dos *hooks* leen el esquema de color del sistema y devuelven la paleta correcta:

{{create:app:src/hooks/use-color-scheme.ts}}

{{create:app:src/hooks/use-theme.ts}}

`ThemedText` es un texto que toma su color del tema y ofrece los estilos tipográficos:

{{create:app:src/components/themed-text.tsx}}

`Screen` respeta las zonas seguras (notch, barra de gestos) y limita el ancho en pantallas grandes. `Button` es accesible: rol de botón, estado `busy`/`disabled` y área táctil mínima de 48 px.

{{create:app:src/components/screen.tsx}}

{{create:app:src/components/button.tsx}}

Por último, un **layout raíz provisional**: solo declara las dos pantallas que crearemos en la semana 9. En la semana 10 lo reemplazaremos por uno que protege las rutas con la sesión.

{{path:app:src/app/_layout.tsx}}
```tsx
import { Stack } from 'expo-router';

/** Versión provisional (semana 9): solo navegación. En la semana 10 se protege con la sesión. */
export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Catálogo' }} />
      <Stack.Screen name="book/[id]" options={{ title: 'Detalle del libro' }} />
    </Stack>
  );
}
```

{{checkpoint:app:base|typecheck,lint}}

> [!NOTA] **Punto de control 0.** `npm run typecheck` y `npx expo lint` sin errores. Si el *typecheck* dice que no encuentra rutas o `expo-env.d.ts`, ejecuta `npx expo start` unos segundos: Expo genera esos archivos de tipos la primera vez.

# 3. Semana 9 · Consumo de API REST

**Del microcurrículo:** *Consumo de API REST desde React Native: HTTP, JSON, asincronía, configuración por ambientes y estados de carga, vacío, error y reintento.* Presencial: comparación guiada del consumo de API en web y móvil. Independiente: integrar la app con la API del proyecto y probar respuestas válidas, errores y pérdida de conectividad.

## 3.1 Conceptos clave

- **HTTP y JSON.** La app envía una petición (método + ruta + cabeceras + cuerpo) y recibe un código de estado y un cuerpo JSON. `2xx` es éxito, `4xx` un problema de la petición y `5xx` del servidor.
- **Asincronía.** `fetch` devuelve una `Promise`; usamos `async/await`. Hay tres desenlaces: respuesta correcta, respuesta con error y *ninguna respuesta*.
- **Timeout.** Sin tiempo máximo, una petición puede quedarse colgada para siempre. Usamos `AbortController` para cancelarla a los 10 segundos.
- **Configuración por ambientes.** La URL de desarrollo no es la de producción. Expo lee `.env` y expone al código las variables con prefijo `EXPO_PUBLIC_`.

> [!OJO] Todo lo que lleve el prefijo `EXPO_PUBLIC_` queda **visible dentro de la app instalada**. Allí van URLs, nunca claves secretas.

### Comparación guiada: consumir una API en web y en móvil

| Aspecto | Web (React en el navegador) | Móvil (React Native) |
|---|---|---|
| Llamada | `fetch` | `fetch` (el mismo) |
| CORS | El navegador lo exige: la API debe permitir el origen | **No existe**: la app no es un navegador |
| `localhost` | El propio computador | **El propio teléfono** |
| HTTP sin cifrar | Los navegadores lo toleran en `localhost` | Android bloquea HTTP en apps publicadas; iOS exige excepciones (ATS) |
| Variables de entorno | `NEXT_PUBLIC_*` / `VITE_*` | `EXPO_PUBLIC_*` |
| Dónde guardar sesión | Cookie `httpOnly` | `expo-secure-store` (Keychain / Keystore) |
| Estado sin red | `navigator.onLine`, caché del navegador | NetInfo y base de datos local (SQLite) |

## 3.2 Paso a paso

### Paso 9.1 · Configuración por ambiente

{{create:app:src/config/env.ts}}

### Paso 9.2 · El contrato de datos (tipos)

Los tipos espejan lo que devuelve la API (Guía 1, paso 9.1). Si la API cambia, TypeScript te avisa en toda la app.

{{create:app:src/types/index.ts}}

### Paso 9.3 · El cliente HTTP

Es la pieza más importante de la semana. Distingue dos clases de fallo, porque la app reacciona distinto a cada una:

- `NetworkError` → no hubo respuesta (sin internet, servidor apagado, timeout). **Se puede reintentar** más tarde.
- `ApiRequestError` → el servidor respondió con un error. Trae `status` y un `code` estable (`NO_COPIES`, `ALREADY_ACTIVE`…).

Otros puntos: el `catch` de `fetch` solo se ejecuta cuando **no hay respuesta**; el timeout limpia su temporizador en el `finally`; y el bloque del `401` (renovar la sesión y reintentar una vez) lo usaremos en la semana 10. El cliente recibe `fetchImpl` por parámetro para poder reemplazarlo en las pruebas.

{{create:app:src/services/api/client.ts}}

### Paso 9.4 · Conectar el cliente con la API (versión provisional)

La API exige sesión, pero todavía no tenemos pantallas de inicio de sesión (son de la semana 10). Mientras tanto, la app entra sola con **tu estudiante de prueba** (el que creaste en la Guía 1). Es un andamio: lo eliminamos en la semana 10.

Para no escribir la contraseña en el código, agrega estas dos líneas a tu archivo `.env` (que no se sube a git; usa tu propio correo y contraseña):

```bash
EXPO_PUBLIC_DEV_EMAIL=estudiante@tucorreo.com
EXPO_PUBLIC_DEV_PASSWORD=TuClaveEstudiante
```

> [!OJO] Todo `EXPO_PUBLIC_*` queda **visible dentro de la app**. Por eso esto es solo provisional y para desarrollo: en la semana 10 las borras y la sesión pasa a ser la del formulario de inicio de sesión.

{{path:app:src/services/api/index.ts}}
```ts
import { API_URL, REQUEST_TIMEOUT_MS } from '@/config/env';
import type { AuthResult } from '@/types';

import { createApiClient } from './client';

/**
 * VERSIÓN PROVISIONAL (semana 9). La API exige un token pero todavía no hay pantallas de inicio de
 * sesión, así que la app entra con tu estudiante de prueba (variables del .env) la primera vez que
 * lo necesita. ⚠️ Se elimina en la semana 10: nunca dejes credenciales en una app real.
 */
const publicApi = createApiClient({ baseUrl: API_URL, timeoutMs: REQUEST_TIMEOUT_MS });

let token: string | null = null;

async function demoLogin(): Promise<string> {
  const email = process.env.EXPO_PUBLIC_DEV_EMAIL;
  const password = process.env.EXPO_PUBLIC_DEV_PASSWORD;
  if (!email || !password) {
    throw new Error('Define EXPO_PUBLIC_DEV_EMAIL y EXPO_PUBLIC_DEV_PASSWORD en el archivo .env');
  }
  const result = await publicApi.post<AuthResult>(
    '/api/auth/login',
    { email, password },
    { auth: false },
  );
  token = result.tokens.idToken;
  return token;
}

export const api = createApiClient({
  baseUrl: API_URL,
  timeoutMs: REQUEST_TIMEOUT_MS,
  auth: {
    getAccessToken: async () => token ?? demoLogin(),
    refreshSession: async () => {
      await demoLogin();
      return true;
    },
  },
});
```

### Paso 9.5 · Los cuatro estados de una pantalla

Toda pantalla que depende de datos remotos debe estar siempre en uno de estos estados: **cargando**, **listo**, **vacío** o **error con reintento**. Los componentes son pequeños y reutilizables. Fíjate en que solo el texto del error se agrupa como alerta, para que el botón *Reintentar* siga siendo enfocable con lectores de pantalla.

{{create:app:src/components/state-views.tsx}}

La decisión de **cuál mostrar** se aísla en una función pura, fácil de probar. Observa la regla central: *si hay datos guardados, siempre se muestran*, aunque la red falle; el error se comunica con un aviso discreto. Esa regla convierte la app en *offline-first* en la semana 11.

{{create:app:src/lib/list-status.ts}}

### Paso 9.6 · Un *hook* para cargar con los cuatro estados

Primera iteración: un *hook* que ejecuta la petición y devuelve `{ state, retry }`. Funciona, pero tiene un defecto que descubrirás al probar con el modo avión: **sin internet no hay catálogo**. En la semana 11 reemplazamos esta fuente por SQLite sin cambiar las pantallas.

{{path:app:src/hooks/use-resource.ts}}
```ts
import { useCallback, useEffect, useState } from 'react';

import { describeError } from '@/services/api/client';

export type ResourceState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'empty' }
  | { status: 'ready'; data: T };

/**
 * Carga un recurso remoto y expone sus cuatro estados (semana 9).
 * `requestKey` identifica la petición (incluye el texto de búsqueda): cuando cambia, se vuelve a cargar.
 */
export function useResource<T>(
  requestKey: string,
  load: () => Promise<T>,
  isEmpty: (data: T) => boolean,
) {
  const [attempt, setAttempt] = useState(0);
  const key = `${requestKey}#${attempt}`;
  const [result, setResult] = useState<{ key: string; state: ResourceState<T> } | null>(null);

  useEffect(() => {
    let active = true; // evita actualizar el estado si la pantalla ya se cerró o la petición quedó obsoleta
    load()
      .then((data) => {
        if (active)
          setResult({
            key,
            state: isEmpty(data) ? { status: 'empty' } : { status: 'ready', data },
          });
      })
      .catch((err) => {
        if (active) setResult({ key, state: { status: 'error', message: describeError(err) } });
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  // Mientras no haya resultado para ESTA petición, el estado es "cargando": no hace falta un setState síncrono.
  const state: ResourceState<T> = result?.key === key ? result.state : { status: 'loading' };
  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { state, retry };
}
```

### Paso 9.7 · Tarjeta y portada del libro

{{create:app:src/components/book-views.tsx}}

### Paso 9.8 · Las pantallas: catálogo y detalle (versión de la semana 9)

El catálogo consume la API directamente. Detalles de calidad móvil ya aplicados: `FlatList` (solo renderiza lo visible), `keyboardShouldPersistTaps="handled"` para que el teclado no se robe el primer toque, `useDeferredValue` para mantener fluida la escritura y accesibilidad en cada elemento.

{{path:app:src/app/index.tsx}}
```tsx
import { useDeferredValue, useState } from 'react';
import { FlatList, StyleSheet, TextInput, View } from 'react-native';

import { BookCard } from '@/components/book-views';
import { Screen } from '@/components/screen';
import { EmptyView, ErrorView, LoadingView } from '@/components/state-views';
import { Spacing } from '@/constants/theme';
import { useResource } from '@/hooks/use-resource';
import { useTheme } from '@/hooks/use-theme';
import { api } from '@/services/api';
import type { Book } from '@/types';

/** Catálogo (semana 9): consume la API directamente y maneja los cuatro estados. */
export default function BooksScreen() {
  const theme = useTheme();
  const [search, setSearch] = useState('');
  const q = useDeferredValue(search);

  const { state, retry } = useResource(
    `books:${q}`,
    () => api.get<{ books: Book[] }>(`/api/books?q=${encodeURIComponent(q.trim())}`),
    (res) => res.books.length === 0,
  );

  return (
    <Screen edges={['left', 'right', 'bottom']}>
      <View style={styles.header}>
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Buscar por título o autor"
          placeholderTextColor={theme.textSecondary}
          accessibilityLabel="Buscar libros por título o autor"
          returnKeyType="search"
          autoCorrect={false}
          style={[
            styles.search,
            {
              color: theme.text,
              borderColor: theme.border,
              backgroundColor: theme.backgroundElement,
            },
          ]}
        />
      </View>

      {state.status === 'loading' ? (
        <LoadingView message="Cargando catálogo…" />
      ) : state.status === 'error' ? (
        <ErrorView message={state.message} onRetry={retry} />
      ) : state.status === 'empty' ? (
        <EmptyView title="Sin resultados" message="Prueba con otro título o autor." />
      ) : (
        <FlatList
          data={state.data.books}
          keyExtractor={(b) => b.id}
          renderItem={({ item }) => <BookCard book={item} />}
          ItemSeparatorComponent={() => <View style={{ height: Spacing.two }} />}
          contentContainerStyle={styles.list}
          keyboardShouldPersistTaps="handled"
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: { paddingVertical: Spacing.two },
  search: {
    minHeight: 48,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: Spacing.three,
    fontSize: 16,
  },
  list: { paddingBottom: Spacing.four },
});
```

{{path:app:src/app/book/[id].tsx}}
```tsx
import { useLocalSearchParams } from 'expo-router';
import { ScrollView, StyleSheet, View } from 'react-native';

import { availabilityLabel, BookCover } from '@/components/book-views';
import { Screen } from '@/components/screen';
import { ErrorView, LoadingView } from '@/components/state-views';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useResource } from '@/hooks/use-resource';
import { useTheme } from '@/hooks/use-theme';
import { api } from '@/services/api';
import type { Book } from '@/types';

/** Detalle del libro (semana 9): solo lectura. El préstamo se agrega en la semana 11. */
export default function BookDetailScreen() {
  const theme = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { state, retry } = useResource(
    `book:${id}`,
    () => api.get<{ book: Book }>(`/api/books/${id}`),
    () => false,
  );

  if (state.status === 'loading') return <LoadingView />;
  if (state.status === 'error') return <ErrorView message={state.message} onRetry={retry} />;
  if (state.status === 'empty') return null; // no ocurre: isEmpty siempre devuelve false

  const { book } = state.data;
  return (
    <Screen edges={['left', 'right', 'bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.cover}>
          <BookCover book={book} width={160} height={220} />
        </View>
        <ThemedText type="subtitle" accessibilityRole="header">
          {book.title}
        </ThemedText>
        <ThemedText themeColor="textSecondary">{book.author}</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          {book.category} · {book.year}
        </ThemedText>
        <ThemedText
          type="smallBold"
          style={{ color: book.availableCopies > 0 ? theme.success : theme.danger }}>
          {availabilityLabel(book)}
        </ThemedText>
        <ThemedText style={styles.description}>{book.description}</ThemedText>
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: { gap: Spacing.two, paddingVertical: Spacing.three },
  cover: { alignItems: 'center', paddingBottom: Spacing.two },
  description: { marginTop: Spacing.two, lineHeight: 24 },
});
```

### Paso 9.9 · Pruebas de la semana

El cliente HTTP es la pieza más crítica, así que tiene pruebas unitarias: el *Bearer token*, los errores del servidor, las respuestas sin JSON (un `502` de un proxy), el timeout, la diferencia entre `NetworkError` y `ApiRequestError`, y el reintento tras `401`. La segunda prueba cubre la decisión de qué estado mostrar.

{{create:app:__tests__/api-client.test.ts}}

{{create:app:__tests__/list-status.test.ts}}

{{checkpoint:app:semana-9|typecheck,lint,test}}

> [!NOTA] **Punto de control de la semana 9.** `npm run typecheck`, `npx expo lint` y `npm test` en verde.

## 3.3 Cómo probar en el teléfono

Con la API encendida (`pnpm dev:lan`) y la URL correcta en `.env`, ejecuta `npx expo start` y escanea el QR con Expo Go. Comprueba cada fila y anótala en tu bitácora:

| Escenario | Cómo provocarlo | Resultado esperado |
|---|---|---|
| Respuesta válida | Abrir la app | Aparecen los 10 libros |
| Estado vacío | Buscar `zzzz` | Mensaje *Sin resultados* |
| Servidor apagado | Detener la API y reabrir la app | Estado de error con botón *Reintentar* |
| Reintento exitoso | Encender la API y tocar *Reintentar* | La lista aparece |
| URL incorrecta | Cambiar `EXPO_PUBLIC_API_URL` a una IP inexistente (y `npx expo start -c`) | Error de conexión en ≤ 10 s, no se congela |
| Detalle | Tocar un libro | Portada, autor, año y disponibilidad |

## 3.4 Evidencia y criterios

> [!EVIDENCIA] Repositorio con la lista y el detalle consumiendo la API; configuración por ambiente (`.env.example`); los cuatro estados visibles y probados; tabla de pruebas manuales completada; `npm test` en verde; entrada de la bitácora de IA.

- [ ] La URL de la API no está escrita en ningún archivo `.ts`
- [ ] Cada fallo de red muestra un mensaje comprensible y nunca deja la pantalla en blanco
- [ ] Hay botón de reintento
- [ ] La petición no queda colgada más de 10 segundos

# 4. Semana 10 · Autenticación, autorización y seguridad

**Del microcurrículo:** *Autenticación, autorización y protección de rutas. Manejo de sesión y tokens con expo-secure-store; secretos, datos personales y registro seguro.* Presencial: modelado de amenazas y laboratorio de autenticación. Independiente: implementar el flujo de acceso y permisos, y contrastar las sugerencias de IA con requisitos de seguridad y pruebas.

## 4.1 Conceptos clave

- **Autenticación** responde *¿quién eres?*; **autorización** responde *¿qué puedes hacer?* (estudiante o bibliotecario).
- **Token de acceso (`idToken`).** JWT firmado por Firebase que la app envía en cada petición. Dura **1 hora** e incluye el rol.
- **Token de renovación (`refreshToken`).** Larga duración; solo sirve para pedir un `idToken` nuevo. Es **el dato más sensible** de la app.
- **¿Dónde guardar los tokens?** `AsyncStorage` y SQLite guardan texto plano legible en un teléfono con root o en una copia de seguridad. `expo-secure-store` usa el Keychain (iOS) y el Keystore (Android), cifrados por el sistema.
- **El cliente nunca es de fiar.** Ocultar un botón es solo experiencia de usuario: la API vuelve a comprobar el rol en cada petición.

### Modelado de amenazas (laboratorio)

Para cada activo: qué podría salir mal y qué control lo reduce. Referencia: OWASP MASVS.

| Activo | Amenaza | Control en este proyecto |
|---|---|---|
| Tokens de sesión | Lectura desde una copia de seguridad o un teléfono con root | Solo en `expo-secure-store`, cada token en su propia llave |
| Contraseña | Se guarda o se imprime en logs | Nunca se persiste; solo viaja en el login por HTTPS |
| Rol del usuario | Un estudiante modifica la app para verse como bibliotecario | La API valida el rol del token en cada petición (`403`) |
| Préstamos de otro usuario | Un estudiante pide por id un préstamo ajeno | La API responde `404` como si no existiera |
| Datos de otra cuenta en el mismo teléfono | Un segundo usuario inicia sesión y hereda la cola de solicitudes | Al cambiar de cuenta se descartan préstamos y cola locales (semana 11) |
| Token robado en tránsito | Red Wi-Fi hostil | HTTPS en producción (HTTP solo en desarrollo) |
| Sesión eterna | Un `refreshToken` robado vive para siempre | La API puede revocarlo; al recibir `401/403` la app cierra la sesión |
| Registro abusivo | Alguien se registra como bibliotecario | El registro público **siempre** crea estudiantes |

## 4.2 Paso a paso

### Paso 10.1 · El gestor de sesión

Toda la lógica de sesión vive en una clase **sin dependencias de React**, lo que permite probarla fácilmente. Tres decisiones importantes:

- **Cada token en su propia llave:** iOS puede rechazar valores de SecureStore de más de ~2 KB y un `idToken` ronda 1 KB.
- **Renovación proactiva y única:** se renueva un minuto *antes* de que venza y, si cinco peticiones reciben `401` juntas, **comparten una sola renovación** (el `refreshToken` rota: enviar cinco rompería algunas).
- **Sin red no se cierra la sesión.** Un fallo de red no significa que la sesión sea inválida; solo un `401/403` del servidor la cierra. Restaurarla al abrir la app tampoco necesita internet.

{{create:app:src/services/auth/session-manager.ts}}

### Paso 10.2 · Conectar la sesión con el cliente HTTP

Reemplaza el archivo provisional de la semana 9. Ahora hay **dos** clientes: uno público (login, registro y refresh) y uno autenticado que agrega el *Bearer*, renueva el token en `401` y reintenta una vez. El de renovación no puede depender de sí mismo.

{{create:app:src/services/api/index.ts}}

> [!OJO] Ya no existe el inicio de sesión automático: **borra del `.env` las líneas `EXPO_PUBLIC_DEV_EMAIL` y `EXPO_PUBLIC_DEV_PASSWORD`** (ya no se usan) y nunca dejes credenciales en una app. Desde ahora entras con el formulario de inicio de sesión, con tus usuarios de prueba.

### Paso 10.3 · Servicio de autenticación y validación

Validamos en el cliente para dar respuesta inmediata, pero la API vuelve a validar todo.

{{create:app:src/services/auth/auth-service.ts}}

### Paso 10.4 · Proveedor de sesión

La suscripción a `session` es la clave: **cualquier** cambio de sesión (login, logout o un cierre forzado porque el `refreshToken` ya no sirve) actualiza el estado y las rutas reaccionan solas.

{{create:app:src/providers/auth-provider.tsx}}

### Paso 10.5 · Campo de texto accesible

{{create:app:src/components/text-field.tsx}}

### Paso 10.6 · Rutas protegidas con `Stack.Protected`

Expo Router permite declarar qué pantallas **existen** según una condición (`guard`). Con la sesión cerrada solo existen `sign-in` y `sign-up`; con la sesión abierta, el catálogo y el detalle. La pantalla de carga nativa se mantiene hasta saber si hay una sesión guardada, para que no parpadee el login.

{{path:app:src/app/_layout.tsx}}
```tsx
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { Pressable } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { AuthProvider, useAuth } from '@/providers/auth-provider';

// La pantalla de carga nativa permanece hasta saber si hay una sesión guardada.
SplashScreen.preventAutoHideAsync();

function RootStack() {
  const { status, signOut } = useAuth();

  useEffect(() => {
    if (status !== 'loading') SplashScreen.hideAsync();
  }, [status]);

  if (status === 'loading') return null;
  const signedIn = status === 'signedIn';

  return (
    <Stack>
      {/* Rutas protegidas (semana 10): el guard decide qué pantallas existen según la sesión. */}
      <Stack.Protected guard={!signedIn}>
        <Stack.Screen name="sign-in" options={{ headerShown: false }} />
        <Stack.Screen name="sign-up" options={{ title: 'Crear cuenta' }} />
      </Stack.Protected>
      <Stack.Protected guard={signedIn}>
        <Stack.Screen
          name="index"
          options={{
            title: 'Catálogo',
            headerRight: () => (
              <Pressable
                onPress={() => void signOut()}
                accessibilityRole="button"
                accessibilityLabel="Cerrar sesión">
                <ThemedText type="linkPrimary">Salir</ThemedText>
              </Pressable>
            ),
          }}
        />
        <Stack.Screen name="book/[id]" options={{ title: 'Detalle del libro' }} />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootStack />
    </AuthProvider>
  );
}
```

> [!OJO] Las rutas protegidas son una comodidad de **navegación**, no una barrera de seguridad. La seguridad real está en la API: sin un token válido no se obtiene ningún dato.

### Paso 10.7 · Pantallas de inicio de sesión y registro

El botón queda en estado `loading` (evita el doble envío), los errores se anuncian con `accessibilityRole="alert"` y la navegación **no** está aquí: al cambiar la sesión, `Stack.Protected` hace el resto.

{{create:app:src/app/sign-in.tsx}}

{{create:app:src/app/sign-up.tsx}}

### Paso 10.8 · Pruebas de la semana

Sesión: restauración sin red, tokens en llaves separadas, `clear()` notifica a los suscriptores, renovación proactiva, **una sola** renovación en vuelo, sesión conservada sin red y cierre de sesión ante `401`. Componentes: estados de pantalla, botones y campos, incluida la accesibilidad.

{{create:app:__tests__/session-manager.test.ts}}

{{create:app:__tests__/components.test.tsx}}

{{checkpoint:app:semana-10|typecheck,lint,test}}

> [!NOTA] **Punto de control de la semana 10.** `npm run typecheck`, `npx expo lint` y `npm test` en verde.

## 4.3 Cómo probar en el teléfono

| Escenario | Resultado esperado |
|---|---|
| Abrir la app sin sesión | Pantalla de inicio de sesión |
| Registrar un estudiante nuevo | Entra al catálogo |
| Registrar un correo ya usado | Mensaje *Ya existe una cuenta con ese correo* |
| Contraseña de 5 caracteres en registro | Error de validación en el campo, sin llamar a la API |
| Iniciar sesión, cerrar la app por completo y abrirla | Sigue con la sesión iniciada (también sin internet) |
| Tocar *Salir* | Vuelve al login |
| Credenciales erróneas | Mensaje *Correo o contraseña incorrectos* |
| Con la API apagada, intentar iniciar sesión | *No hay conexión con el servidor…* |

## 4.4 Evidencia y criterios

> [!EVIDENCIA] Flujo de registro, inicio y cierre de sesión funcionando; tokens en `expo-secure-store`; rutas protegidas; tabla de modelado de amenazas completada para tu proyecto; pruebas de sesión en verde; bitácora de IA con al menos una sugerencia **contrastada** contra estos requisitos de seguridad.

- [ ] Ningún token ni contraseña aparece en la consola ni en SQLite
- [ ] La sesión sobrevive al reinicio de la app
- [ ] Un `401` provoca una renovación y un reintento, no una pantalla de error
- [ ] No queda ninguna credencial en el código ni en el `.env` de la app

# 5. Semana 11 · SQLite, sincronización y trabajo sin conexión

**Del microcurrículo:** *Sincronización local-remota: caché, cola de cambios, detección de conectividad, conflictos y consistencia eventual. Estrategias offline-first básicas.* Presencial: estudio de casos y laboratorio de sincronización. Independiente: implementar lectura local, actualización remota y recuperación; diseñar y probar escenarios de reconexión y conflicto.

## 5.1 Conceptos clave

- **Offline-first.** La interfaz lee y escribe en la base de datos local; la red es un detalle que se resuelve en segundo plano.
- **Caché.** Copia local del catálogo para mostrarlo al instante y sin conexión.
- **Cola de cambios (*outbox*).** Tabla donde se anotan los cambios hechos sin conexión, en orden, hasta enviarlos.
- **Sincronización incremental.** En vez de descargar todo, se envía al servidor un *cursor* (`updatedSince`) y este devuelve solo lo que cambió.
- **Idempotencia.** Enviar la **misma** solicitud dos veces no debe crear dos préstamos. Cada solicitud lleva un `clientRequestId` (UUID) generado en el teléfono; si el servidor ya lo vio, devuelve la existente. Hace seguro reintentar tras perder la respuesta.
- **Consistencia eventual.** Durante un rato el teléfono y el servidor pueden diferir; al sincronizar convergen.
- **Resolución de conflictos.** Aquí aplicamos *"gana el servidor"*: es simple, predecible y suficiente, porque el servidor es quien conoce los ejemplares reales.

### El ciclo completo

{{diagram:sync}}

### Modelo de datos local

| Tabla | Para qué sirve | Detalle clave |
|---|---|---|
| `books` | Caché del catálogo | `search_text` (título + autor sin tildes) para buscar sin importar acentos |
| `loans` | Préstamos, incluidos los aún no enviados | `sync_state`: `synced`, `pending` o `conflict`; `client_request_id` único |
| `outbox` | Cola de cambios sin enviar | `attempts` y `last_error` para reintentos |
| `sync_meta` | Clave/valor | Cursor de libros, fecha de última sincronización, dueño de los datos |
| `activity_log` | Bitácora de eventos | Trazabilidad (semana 12); solo los últimos 200 |

## 5.2 Paso a paso

### Paso 11.1 · Utilidades de texto

`normalizeSearch` quita tildes y mayúsculas; `escapeLike` hace que un `%` escrito por el usuario se busque como texto y no como comodín de SQL.

{{create:app:src/lib/text.ts}}

### Paso 11.2 · Migraciones con `PRAGMA user_version`

SQLite guarda un número de versión dentro del archivo. Al abrir la app lo comparamos con `DATABASE_VERSION` y aplicamos, en orden, **solo lo que falta**. Así un teléfono con la versión 1 de la app se actualiza sin perder datos al instalar la versión 2.

{{create:app:src/db/migrations.ts}}

> [!OJO] **Nunca edites una migración que ya se publicó.** Agrega una nueva (`if (version < 3)`) y sube `DATABASE_VERSION`. Cada migración corre dentro de una transacción: o se aplica completa o no se aplica.

### Paso 11.3 · Repositorios: toda la SQL en un solo lugar

Las pantallas nunca arman consultas. Los repositorios exponen operaciones con nombre de negocio y **todas las consultas son parametrizadas** (`?`): nunca se concatena texto del usuario. Puntos para leer con calma:

- `upsertMany` usa una **transacción** (entran todos los libros o ninguno).
- `upsertFromServer` reemplaza la copia local (mismo `client_request_id`) por la del servidor: así un préstamo creado sin conexión **nunca queda duplicado**.
- La cola `outbox` es FIFO con conteo de intentos.

{{create:app:src/db/repositories.ts}}

### Paso 11.4 · Solicitar un préstamo, con o sin internet

El servicio aplica primero las reglas que ya puede comprobar **en el teléfono** y luego guarda; no espera a la red. Fíjate en el orden: primero la cola y después el préstamo local. Si la app se cierra entre ambos pasos, la sincronización igual envía la solicitud y trae el préstamo desde el servidor; nunca queda un préstamo "fantasma" sin cola.

{{create:app:src/services/loans/loan-service.ts}}

### Paso 11.5 · El servicio de sincronización

Es el archivo central de la semana. Primero **envía** la cola; después **descarga** libros (incremental) y préstamos. Qué hace ante cada respuesta al enviar una solicitud:

| Respuesta | Qué hace la app |
|---|---|
| `200` / `201` | Reemplaza la copia local por la del servidor y quita el elemento de la cola |
| `409` (`NO_COPIES`, `ALREADY_ACTIVE`) o `404` | **Conflicto**: marca el préstamo `conflict` con un mensaje claro y lo quita de la cola. No bloquea las demás solicitudes |
| Sin conexión | Conserva **toda** la cola y propaga el error |
| `5xx` o `429` | Suma un intento y reintenta en la próxima sincronización; tras 5 intentos lo marca como no procesable |
| `401` | No es un conflicto del préstamo: se conserva la cola y se renueva la sesión |

El cursor de libros se guarda con **1 segundo de solape**: pedir un poco "hacia atrás" evita perder un cambio ocurrido justo en el borde, y como el *upsert* es idempotente, repetir un libro no causa daño.

{{create:app:src/services/sync/sync-service.ts}}

### Paso 11.6 · Cuándo sincronizar: conectividad y ciclo de vida

`DataProvider` decide los momentos de sincronización: al iniciar sesión, al volver la red (NetInfo), al volver la app a primer plano, al deslizar para refrescar y justo después de solicitar un préstamo. Garantiza **un solo ciclo a la vez**. Además, los datos privados pertenecen a **una cuenta**: si cambió el usuario, se descartan los préstamos y la cola anteriores para no enviar solicitudes a nombre de otra persona; y al cerrar sesión se borran los datos privados del dispositivo (el catálogo público se conserva).

{{create:app:src/providers/data-provider.tsx}}

### Paso 11.7 · La interfaz solo lee de SQLite

Los *hooks* consultan la base local y vuelven a consultar cuando `dataVersion` cambia (lo incrementa el proveedor tras cada sincronización o escritura).

{{create:app:src/hooks/use-library-data.ts}}

### Paso 11.8 · Comunicar el estado al usuario

El aviso no bloquea nada; informa y permite reintentar con un toque. La tarjeta de préstamo muestra el estado real: **Pendiente de envío**, **Solicitado**, **Prestado**, **Devuelto** o **No se pudo solicitar** (con el motivo y un botón *Descartar*).

{{create:app:src/components/connection-banner.tsx}}

{{create:app:src/components/loan-card.tsx}}

> [!IDEA] **Decisión de diseño documentada:** el estudiante puede solicitar sin conexión, pero el bibliotecario necesita conexión para prestar o devolver. Prestar modifica el inventario compartido y debe decidirse con datos actuales; permitirlo sin conexión generaría conflictos mucho más difíciles de resolver. Los botones se deshabilitan sin internet con una explicación.

### Paso 11.9 · Pantallas definitivas: pestañas, préstamos y perfil

Ya no necesitamos la pantalla provisional ni el *hook* de la semana 9. Elimínalos y crea las pestañas:

{{delete:app:src/app/index.tsx}}

{{delete:app:src/hooks/use-resource.ts}}

{{create:app:src/app/(tabs)/_layout.tsx}}

El catálogo ahora lee de SQLite, con búsqueda sin tildes, filtro por categoría y deslizar para sincronizar:

{{create:app:src/app/(tabs)/index.tsx}}

*Mis préstamos* (estudiante) o *Gestión* (bibliotecario, con las acciones prestar, rechazar y devolver):

{{create:app:src/app/(tabs)/loans.tsx}}

El perfil muestra el estado de sincronización, la actividad reciente y cierra sesión (avisando si hay solicitudes sin enviar):

{{create:app:src/app/(tabs)/profile.tsx}}

El detalle del libro, ahora con el botón **Solicitar préstamo** y el estado de la solicitud (la gestión de portadas llega en la semana 12):

{{path:app:src/app/book/[id].tsx}}
```tsx
import { useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';

import { availabilityLabel, BookCover } from '@/components/book-views';
import { Button } from '@/components/button';
import { Screen } from '@/components/screen';
import { EmptyView, LoadingView } from '@/components/state-views';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useBook, useMyLoanForBook } from '@/hooks/use-library-data';
import { useTheme } from '@/hooks/use-theme';
import { useAuth } from '@/providers/auth-provider';
import { useData } from '@/providers/data-provider';
import { describeError } from '@/services/api/client';
import { LoanRuleError } from '@/services/loans/loan-service';

export default function BookDetailScreen() {
  const theme = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { user } = useAuth();
  const { online, requestLoan } = useData();
  const { book, loaded } = useBook(id);
  const myLoan = useMyLoanForBook(id);

  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ text: string; error: boolean } | null>(null);

  if (!loaded) return <LoadingView />;
  if (!book)
    return <EmptyView title="Libro no encontrado" message="Puede que ya no esté en el catálogo." />;

  const librarian = user?.role === 'librarian';
  const hasActive =
    myLoan &&
    myLoan.syncState !== 'conflict' &&
    (myLoan.status === 'requested' || myLoan.status === 'approved');

  async function onRequest() {
    if (!book) return;
    setBusy(true);
    setFeedback(null);
    try {
      await requestLoan(book);
      setFeedback({
        error: false,
        text: online
          ? 'Solicitud registrada. Se está enviando al servidor.'
          : 'Sin conexión: tu solicitud quedó guardada y se enviará automáticamente cuando vuelva internet.',
      });
    } catch (err) {
      setFeedback({
        error: true,
        text: err instanceof LoanRuleError ? err.message : describeError(err),
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen edges={['left', 'right', 'bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.cover}>
          <BookCover book={book} width={160} height={220} />
        </View>

        <ThemedText type="subtitle" accessibilityRole="header">
          {book.title}
        </ThemedText>
        <ThemedText themeColor="textSecondary">{book.author}</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          {book.category} · {book.year}
        </ThemedText>
        <ThemedText
          type="smallBold"
          style={{ color: book.availableCopies > 0 ? theme.success : theme.danger }}>
          {availabilityLabel(book)}
        </ThemedText>
        <ThemedText style={styles.description}>{book.description}</ThemedText>

        {!librarian ? (
          <View style={styles.actions}>
            {myLoan && myLoan.syncState === 'pending' ? (
              <ThemedText type="smallBold" style={{ color: theme.warning }}>
                Solicitud guardada · pendiente de envío
              </ThemedText>
            ) : null}
            {myLoan && myLoan.syncState === 'conflict' ? (
              <ThemedText
                type="smallBold"
                style={{ color: theme.danger }}
                accessibilityRole="alert">
                Tu última solicitud no se pudo procesar: {myLoan.syncError}
              </ThemedText>
            ) : null}
            {myLoan?.syncState === 'synced' && myLoan.status === 'requested' ? (
              <ThemedText type="smallBold" style={{ color: theme.primary }}>
                Solicitud enviada · esperando al bibliotecario
              </ThemedText>
            ) : null}
            {myLoan?.syncState === 'synced' && myLoan.status === 'approved' ? (
              <ThemedText type="smallBold" style={{ color: theme.success }}>
                Tienes este libro prestado
              </ThemedText>
            ) : null}
            <Button
              title={book.availableCopies > 0 ? 'Solicitar préstamo' : 'Sin ejemplares disponibles'}
              disabled={book.availableCopies <= 0 || !!hasActive}
              loading={busy}
              onPress={onRequest}
              accessibilityHint="Envía una solicitud de préstamo al bibliotecario"
            />
          </View>
        ) : null}

        {feedback ? (
          <ThemedText
            accessibilityLiveRegion="polite"
            accessibilityRole={feedback.error ? 'alert' : undefined}
            style={{ color: feedback.error ? theme.danger : theme.success }}>
            {feedback.text}
          </ThemedText>
        ) : null}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: { gap: Spacing.two, paddingVertical: Spacing.three },
  cover: { alignItems: 'center', paddingBottom: Spacing.two },
  description: { marginTop: Spacing.two, lineHeight: 24 },
  actions: { gap: Spacing.two, marginTop: Spacing.three },
});
```

Por último, el **layout raíz definitivo**: abre y migra la base de datos *antes* que todo lo demás (`SQLiteProvider` con `onInit`), y envuelve la app con la sesión y los datos. El orden importa: la sesión y los datos dependen de la base de datos.

{{create:app:src/app/_layout.tsx}}

### Paso 11.10 · Pruebas de la semana

SQLite no corre dentro de Jest, pero Node 24 incluye `node:sqlite`. El archivo `node-sqlite.ts` expone la misma interfaz que `expo-sqlite` sobre ese motor, así que **las consultas reales** se prueban sin dispositivo. `fakes.ts` aporta datos de prueba y repositorios en memoria.

{{create:app:test-utils/node-sqlite.ts}}

{{create:app:test-utils/fakes.ts}}

- `database.test.ts`: migración desde cero, idempotente, y **actualización v1 → v2 sin perder datos**; búsqueda sin tildes; un `%` o una comilla no rompen el SQL; reemplazo de la copia local; restricción `CHECK` de estados.
- `sync-service.test.ts`: orden FIFO, sin conexión conserva la cola, conflicto `409`, `5xx` con reintentos, `401`, cursor incremental, el cursor no avanza si la descarga falla.
- `offline-flow.test.ts`: los escenarios de reconexión, conflicto e idempotencia de punta a punta con SQL real.

{{create:app:__tests__/text.test.ts}}

{{create:app:__tests__/database.test.ts}}

{{create:app:__tests__/sync-service.test.ts}}

{{create:app:__tests__/offline-flow.test.ts}}

{{checkpoint:app:semana-11|typecheck,lint,test}}

> [!NOTA] **Punto de control de la semana 11.** `npm run typecheck`, `npx expo lint` y `npm test` en verde (8 archivos de pruebas).

## 5.3 Escenarios de prueba en el teléfono

### Escenario A · Reconexión

1. Inicia sesión como estudiante con internet y espera a que cargue el catálogo.
2. Activa el **modo avión**. Verás el aviso *Sin conexión · Mostrando datos guardados*.
3. Abre un libro y pulsa **Solicitar préstamo**. Aparece *"Solicitud guardada… se enviará cuando vuelva internet"*.
4. En *Mis préstamos* la solicitud dice **Pendiente de envío**; en *Perfil*, *Cambios pendientes: 1*.
5. Desactiva el modo avión. En unos segundos la solicitud pasa a **Solicitado** y el contador vuelve a 0.

### Escenario B · Conflicto

1. En el libro **Rayuela** (1 ejemplar), entra como estudiante con internet y espera la sincronización.
2. Activa el modo avión y solicita Rayuela: queda *Pendiente de envío*.
3. Desde otro dispositivo o desde el sitio web, entra como **otro estudiante**, solicita Rayuela y haz que el **bibliotecario la apruebe**. Ahora no quedan ejemplares.
4. Desactiva el modo avión en el primer teléfono. El servidor responde `409 NO_COPIES`.
5. Resultado esperado: tu solicitud queda **No se pudo solicitar** con el motivo *"Cuando se envió tu solicitud ya no quedaban ejemplares disponibles"*, el catálogo muestra Rayuela sin ejemplares y puedes *Descartar* el aviso.

### Escenario C · Reintento sin duplicados

Si el teléfono pierde la señal justo después de enviar, la app reenvía la solicitud con el mismo `clientRequestId`; el servidor devuelve la existente y en la base de datos **no** aparecen dos préstamos (lo prueba `offline-flow.test.ts`).

## 5.4 Evidencia y criterios

> [!EVIDENCIA] Modo avión funcionando (catálogo visible, solicitud en cola); video corto o capturas de los escenarios A y B; migraciones y repositorios; pruebas de sincronización en verde; documento breve que justifique la estrategia de conflictos ("gana el servidor").

- [ ] La app arranca y muestra el catálogo sin internet después de la primera sincronización
- [ ] Una solicitud hecha sin conexión se envía sola al volver la red
- [ ] Reintentar nunca crea préstamos duplicados
- [ ] Un conflicto se explica al usuario con un mensaje claro
- [ ] Cerrar sesión borra préstamos y cola del teléfono

# 6. Semana 12 · Servicio del dispositivo integrado con la API

**Del microcurrículo:** *Integración de un servicio del dispositivo con la API: imágenes, ubicación o notificaciones. Permisos, validación, manejo de fallos y trazabilidad.* Presencial: demostración de integración y pruebas en dispositivo. Entrega y sustentación del **hito 3**.

Elegimos **imágenes**: el bibliotecario toma una foto (o elige una de la galería) y la usa como portada de un libro. Es una integración completa: permiso → captura → procesamiento → subida a la API → actualización de la interfaz.

## 6.1 Conceptos clave

- **Mínimo privilegio.** Se declara solo el permiso de cámara; el micrófono se desactiva. La galería usa el selector del sistema, que **no requiere permiso de almacenamiento**.
- **Permiso en contexto.** No se pide al abrir la app: se pide cuando el usuario pulsa *Tomar foto*, momento en el que entiende por qué.
- **Permiso denegado para siempre.** Si el usuario marcó "No volver a preguntar", el sistema no muestra más el diálogo; la única salida es enviarlo a **Ajustes**.
- **Validar antes y después.** La app reduce y comprime; la API revisa el tamaño y los **bytes reales** del archivo.
- **Trazabilidad.** Cada paso queda en `activity_log` y se muestra en *Perfil → Actividad reciente*, sin guardar la imagen ni datos personales.

## 6.2 Paso a paso

### Paso 12.1 · Declarar los permisos (plugin de Expo)

Los textos que ve el usuario se configuran en `app.json`. Esta es la lista **completa** de plugins del proyecto (se reemplaza el arreglo completo; los de SQLite y SecureStore los agregó `expo install`). Cambiarlos exige una nueva compilación nativa; en Expo Go ya vienen configurados por Expo.

{{merge:app:app.json}}
```json
{
  "expo": {
    "plugins": [
      "expo-router",
      [
        "expo-splash-screen",
        {
          "backgroundColor": "#208AEF",
          "image": "./assets/images/splash-icon.png",
          "imageWidth": 76
        }
      ],
      "expo-sqlite",
      "expo-secure-store",
      [
        "expo-image-picker",
        {
          "cameraPermission": "Biblioteca usa la cámara para tomar la foto de portada de un libro.",
          "photosPermission": "Biblioteca accede a tus fotos solo cuando eliges una portada.",
          "microphonePermission": false
        }
      ]
    ]
  }
}
```

### Paso 12.2 · El servicio de cámara y subida

La foto original puede pesar varios MB: se reduce a 600 px de ancho y se prueban calidades decrecientes hasta que cabe en el límite de la API (≈ 520 KB). `PermissionDeniedError` distingue si se puede volver a preguntar (`canAskAgain`).

{{create:app:src/services/device/cover-service.ts}}

### Paso 12.3 · La pantalla del libro, versión definitiva

Reemplaza el detalle de la semana 11. Añade los botones del bibliotecario y traduce cada fallo a una respuesta útil. Cuando se sube la portada se actualiza **también la base local** (`upsertMany`): así aparece en la lista sin esperar otra sincronización, y los demás dispositivos la reciben en la suya porque el servidor sube `updatedAt` del libro.

{{create:app:src/app/book/[id].tsx}}

{{checkpoint:app:semana-12|typecheck,lint,test,export}}

> [!NOTA] **Punto de control de la semana 12.** `npm run typecheck`, `npx expo lint`, `npm test` y la exportación del paquete (`npx expo export`) sin errores.

## 6.3 Manejo de fallos: qué ve el usuario

| Situación | Comportamiento |
|---|---|
| Permiso de cámara denegado (se puede volver a preguntar) | Alerta explicativa; sigue disponible *Elegir de la galería* |
| Denegado definitivamente | Alerta con botón **Abrir ajustes** |
| Usuario cancela la cámara | No pasa nada, sin mensajes de error |
| Sin conexión | Mensaje *Necesitas conexión para subir la portada* (esta acción no se encola) |
| Imagen demasiado grande tras comprimir | Mensaje pidiendo otra imagen |
| Servidor rechaza el archivo (`400`/`403`) | Se muestra el mensaje del servidor |
| Un estudiante intenta la acción | La API responde `403`; la interfaz ni siquiera muestra los botones |

## 6.4 Trazabilidad

Eventos que quedan registrados en SQLite (visibles en *Perfil → Actividad reciente*):

```text
cover.permission · cámara: granted
cover.pick       · camera: 148 KB base64, calidad 0.7
cover.upload     · OK libro clean-code
sync             · Enviadas 1, en conflicto 0
loan.approve     · Préstamo de "Clean Code" → approved
```

> [!OJO] La bitácora **nunca** guarda la imagen, tokens ni datos personales: solo el tipo de evento y datos técnicos.

## 6.5 Pruebas en dispositivo (lista de verificación)

El servicio de cámara no se puede probar en un simulador (el de iOS no tiene cámara). Marca cada prueba en un teléfono real:

- [ ] Como bibliotecario, *Tomar foto* pide permiso la primera vez
- [ ] Rechazar el permiso muestra la alerta y la galería sigue funcionando
- [ ] Conceder el permiso abre la cámara; cancelar no produce errores
- [ ] La portada tomada aparece en el detalle y en la lista de libros
- [ ] Otro dispositivo ve la portada tras sincronizar
- [ ] Con modo avión, intentar subir muestra el mensaje de conexión
- [ ] Como estudiante no existen los botones de portada
- [ ] *Perfil → Actividad reciente* muestra los eventos `cover.*`

## 6.6 Evidencia del hito 3

> [!EVIDENCIA] **Hito 3 (semana 12, 15 %):** aplicación integrada con API REST, autenticación y almacenamiento seguro de sesión, sincronización local-remota, manejo de conectividad y un servicio del dispositivo; pruebas de escenarios críticos y documentación; sustentación individual.

Prepárate para explicar y **modificar en vivo**:

- Cómo viaja una solicitud de préstamo desde el toque del botón hasta Firestore, y qué pasa si falla cada tramo.
- Por qué los tokens están en SecureStore y qué ocurre con un `401`.
- Qué es `clientRequestId` y qué problema resuelve.
- Qué pasa con una solicitud hecha sin conexión cuando el ejemplar se agota.
- Cómo agregarías una columna a `books` con una migración nueva.

# 7. Pruebas de integración y calidad

## 7.1 La app real contra la API real

Esta prueba ejecuta **el código de la app** (cliente HTTP, sesión, SQLite, cola y sincronización) contra tu API y Firebase. Verifica el flujo estudiante → bibliotecario → estudiante y la recuperación automática de un token vencido. Solo corre si defines la URL de la API **y** las credenciales de un estudiante y un bibliotecario tuyos, por variables de entorno (así no queda ninguna credencial en el repositorio). `node-fetch.ts` es un `fetch` real sobre `node:http` (el entorno de Jest sustituye el global por un simulacro).

{{create:app:test-utils/node-fetch.ts}}

{{create:app:__tests__/e2e-api.test.ts}}

```bash
# (en library_api)  pnpm seed && pnpm dev
E2E_API_URL=http://localhost:3000 \
E2E_STUDENT_EMAIL=estudiante@tucorreo.com E2E_STUDENT_PASSWORD=TuClaveEstudiante \
E2E_LIBRARIAN_EMAIL=bibliotecario@tucorreo.com E2E_LIBRARIAN_PASSWORD=TuClaveBibliotecario \
npx jest e2e-api
# (en library_api)  pnpm reset-demo      ← deja los datos como al inicio
```

## 7.2 Verificación completa

{{run:app}}
```bash
npm run typecheck
npx expo lint
npm test
```

{{checkpoint:app:final|typecheck,lint,test,export}}

> [!NOTA] **Punto de control final.** Los comandos sin errores (las pruebas de integración se omiten si no defines las variables `E2E_*`). Tu app está completa.

## 7.3 Qué cubren las pruebas

| Archivo | Qué protege |
|---|---|
| `api-client.test.ts` | Errores tipados, timeout, reintento tras 401, respuestas sin JSON |
| `session-manager.test.ts` | Almacenamiento seguro, renovación única, sesión sin red |
| `sync-service.test.ts` | Cola, conflictos, reintentos, cursor incremental |
| `database.test.ts` | Migraciones, consultas, búsqueda, restricciones (SQL real) |
| `offline-flow.test.ts` | Reconexión, conflicto e idempotencia de punta a punta |
| `components.test.tsx` | Estados de pantalla, botones, campos y accesibilidad |
| `list-status.test.ts`, `text.test.ts` | Reglas puras de estados y búsqueda |
| `e2e-api.test.ts` | La app real contra la API real (solo con las variables `E2E_*`) |

> [!NOTA] Las pruebas automáticas **no sustituyen** la prueba en un teléfono real: no cubren permisos del sistema, cámara, rendimiento ni la experiencia táctil. Hazlas siempre antes de entregar.

# 8. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Network request failed` o *No hay conexión con el servidor* | `EXPO_PUBLIC_API_URL` usa `localhost` en un teléfono, IP incorrecta, otra red Wi-Fi o firewall | Usa la IP del PC, misma red, `pnpm dev:lan`, abre el puerto 3000; reinicia con `npx expo start -c` |
| Funciona en el navegador del PC pero no en el teléfono | La API escucha solo en `localhost` | Arranca con `pnpm dev:lan` |
| En WSL2 no conecta desde el teléfono | WSL2 está en red NAT | `networkingMode=mirrored` o `netsh interface portproxy` (ver 1.4) |
| El cambio de `.env` no se nota | Metro guarda caché | `npx expo start -c` |
| `Correo o contraseña incorrectos` con tus usuarios de prueba | No creaste el usuario con `pnpm create-user` o Authentication no está habilitado | Revisa la Guía 1 (secciones 2.5 y 4.4) |
| Un bibliotecario recién asignado sigue viendo opciones de estudiante | Su token aún no se renovó | Cerrar sesión y volver a entrar |
| La app pide sesión cada vez | `expo-secure-store` falló o hubo `401` al renovar | Revisa los logs de la API; vuelve a iniciar sesión |
| Las portadas no se ven | La URL de la API es inalcanzable desde el teléfono | Es la misma URL de `.env`; prueba abrirla en el navegador del teléfono |
| `typecheck` no encuentra `expo-env.d.ts` o las rutas tipadas | Aún no se generaron los tipos de Expo | Ejecuta `npx expo start` unos segundos |
| `expo-sqlite` no funciona en web | SQLite nativo no está soportado en esta app para web | Prueba en Android o iOS |
| `Error al subir portada: imagen demasiado grande` | Fotografía muy pesada | La app ya comprime; prueba con otra imagen |

# 9. Bitácora de uso de IA generativa

El microcurrículo exige registrar cada uso de IA con **propósito, evidencia, validación y decisión**. Úsala para explorar, explicar, depurar, generar casos de prueba o documentar, pero tú debes poder explicar y modificar cada línea que entregues.

| Fecha | Herramienta y prompt (resumido) | Qué respondió | Cómo lo validé | Decisión |
|---|---|---|---|---|
| (ej.) Sem. 10 | *"¿Dónde guardo el refreshToken en Expo?"* | Sugirió `AsyncStorage` | Contrasté con la guía de MASVS y la documentación de Expo: no es almacenamiento seguro | Rechazada; usé `expo-secure-store` |
| (ej.) Sem. 11 | *"Genera casos de prueba para una cola offline"* | 8 casos | Ejecuté los casos; 2 fallaron por un error de mi servicio, no del caso | Aceptada con ajustes; corregí el servicio |
| | | | | |

Buenas prácticas: no pegues credenciales, el `.env` ni datos personales en un asistente; verifica siempre contra la **documentación oficial** y ejecutando en un dispositivo; guarda el enlace o la captura como evidencia.

# 10. Referencias

- React Native. *Accessibility*. https://reactnative.dev/docs/accessibility
- Expo. *Expo Router: protected routes*. https://docs.expo.dev/router/advanced/protected/
- Expo. *Expo SQLite*. https://docs.expo.dev/versions/latest/sdk/sqlite/
- Expo. *Expo SecureStore*. https://docs.expo.dev/versions/latest/sdk/securestore/
- Expo. *NetInfo*. https://docs.expo.dev/versions/latest/sdk/netinfo/
- Expo. *ImagePicker* e *ImageManipulator*. https://docs.expo.dev/versions/latest/sdk/imagepicker/
- Expo. *Unit testing with Jest*. https://docs.expo.dev/develop/unit-testing/
- OWASP. *Mobile Application Security Verification Standard (MASVS)*. https://mas.owasp.org/MASVS/
- UNESCO (2023). *Guidance for generative AI in education and research*. https://unesdoc.unesco.org/ark:/48223/pf0000386693
