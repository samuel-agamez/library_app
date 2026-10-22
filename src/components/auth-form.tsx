import { Link } from 'expo-router';
import { useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';

import { Button } from '@/components/button';
import { Screen } from '@/components/screen';
import { TextField } from '@/components/text-field';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useAuth } from '@/providers/auth-provider';
import { describeError } from '@/services/api/client';
import { validateCredentials } from '@/services/auth/auth-service';

type Mode = 'signIn' | 'signUp';

/**
 * Formulario compartido por las pantallas de inicio de sesión y registro.
 * Solo cambian los campos (nombre en el registro) y los textos.
 */
export function AuthForm({ mode }: { mode: Mode }) {
  const signInMode = mode === 'signIn';
  const theme = useTheme();
  const { signIn, signUp } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ name?: string; email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const emailRef = useRef<TextInput>(null);
  const passwordRef = useRef<TextInput>(null);

  async function submit() {
    const found = validateCredentials({ name, email, password }, mode);
    setErrors(found);
    setFormError(null);
    if (Object.keys(found).length > 0) return;

    setLoading(true);
    try {
      if (signInMode) await signIn(email, password);
      else await signUp(name, email, password);
      // Sin navegación manual: al cambiar la sesión, Stack.Protected lleva a las pestañas.
    } catch (err) {
      setFormError(describeError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen edges={signInMode ? undefined : ['left', 'right']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}>
        <ScrollView
          contentContainerStyle={[styles.form, signInMode && styles.formCentered]}
          keyboardShouldPersistTaps="handled">
          {signInMode ? (
            <>
              <ThemedText type="title" style={styles.title} accessibilityRole="header">
                Biblioteca
              </ThemedText>
              <ThemedText themeColor="textSecondary">
                Inicia sesión para ver y solicitar libros.
              </ThemedText>
            </>
          ) : (
            <ThemedText themeColor="textSecondary">
              Las cuentas nuevas son de estudiante. El rol de bibliotecario lo asigna la
              administración.
            </ThemedText>
          )}

          {signInMode ? null : (
            <TextField
              label="Nombre"
              value={name}
              onChangeText={setName}
              error={errors.name}
              autoComplete="name"
              textContentType="name"
              returnKeyType="next"
              onSubmitEditing={() => emailRef.current?.focus()}
            />
          )}
          <TextField
            ref={emailRef}
            label="Correo"
            value={email}
            onChangeText={setEmail}
            error={errors.email}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            autoCorrect={false}
            textContentType="emailAddress"
            returnKeyType="next"
            onSubmitEditing={() => passwordRef.current?.focus()}
          />
          <TextField
            ref={passwordRef}
            label={signInMode ? 'Contraseña' : 'Contraseña (mínimo 6 caracteres)'}
            value={password}
            onChangeText={setPassword}
            error={errors.password}
            secureTextEntry
            autoComplete={signInMode ? 'current-password' : 'new-password'}
            textContentType={signInMode ? 'password' : 'newPassword'}
            returnKeyType="go"
            onSubmitEditing={submit}
          />

          {formError ? (
            <ThemedText accessibilityRole="alert" style={{ color: theme.danger }}>
              {formError}
            </ThemedText>
          ) : null}

          <Button
            title={signInMode ? 'Iniciar sesión' : 'Crear cuenta'}
            onPress={submit}
            loading={loading}
          />

          {signInMode ? (
            <View style={styles.footer}>
              <ThemedText themeColor="textSecondary">¿No tienes cuenta?</ThemedText>
              <Link href="/sign-up" accessibilityRole="link">
                <ThemedText type="linkPrimary">Regístrate</ThemedText>
              </Link>
            </View>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  form: {
    flexGrow: 1,
    gap: Spacing.three,
    paddingVertical: Spacing.four,
  },
  formCentered: { justifyContent: 'center' },
  title: { fontSize: 40, lineHeight: 46 },
  footer: {
    flexDirection: 'row',
    gap: Spacing.two,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
