const COOKIE_NAME = 'edge_session';
const textEncoder = new TextEncoder();

export function sessionCookieName(): string {
  return COOKIE_NAME;
}

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlToBytes(str: string): Uint8Array {
  const base64 = str.replace(/-/g, '+').replace(/_/g, '/');
  const pad = (4 - (base64.length % 4)) % 4;
  const padded = base64 + '='.repeat(pad);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function timingSafeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a[i] ^ b[i];
  }
  return diff === 0;
}

async function hmac(secret: string, payload: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    'raw',
    textEncoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const signature = await crypto.subtle.sign('HMAC', key, textEncoder.encode(payload));
  return bytesToBase64Url(new Uint8Array(signature));
}

export async function signSessionToken(secret: string, payload: { iatMs: number }): Promise<string> {
  const body = JSON.stringify(payload);
  const bodyB64 = bytesToBase64Url(textEncoder.encode(body));
  const sig = await hmac(secret, bodyB64);
  return `${bodyB64}.${sig}`;
}

export async function verifySessionToken(
  secret: string,
  token: string | undefined | null
): Promise<boolean> {
  if (!token) return false;
  const [bodyB64, sig] = token.split('.');
  if (!bodyB64 || !sig) return false;
  const expected = await hmac(secret, bodyB64);
  try {
    const a = base64UrlToBytes(sig);
    const b = base64UrlToBytes(expected);
    if (!timingSafeEqual(a, b)) return false;
  } catch {
    return false;
  }
  try {
    const payload = JSON.parse(new TextDecoder().decode(base64UrlToBytes(bodyB64))) as {
      iatMs?: number;
    };
    if (!payload?.iatMs) return false;
    if (Date.now() - payload.iatMs > 7 * 24 * 60 * 60 * 1000) return false;
    return true;
  } catch {
    return false;
  }
}
