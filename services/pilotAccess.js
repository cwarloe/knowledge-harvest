// Local, synthetic-only owner pilot. No new dependencies or external identity service.
const crypto = require('crypto');
const path = require('path');

const COOKIE_NAME = 'kh_pilot_session';
const SESSION_MS = 12 * 60 * 60 * 1000;
const LOGIN_WINDOW_MS = 15 * 60 * 1000;

function readPilotConfig(env, defaultUploadsDir) {
  if (!env.KH_PRIVATE_PILOT || env.KH_PRIVATE_PILOT === '0') return null;
  if (env.KH_PRIVATE_PILOT !== '1') {
    throw new Error('KH_PRIVATE_PILOT must be 1 to enable the private pilot, or 0/unset for ordinary development');
  }

  const secret = env.KH_PILOT_ACCESS_TOKEN;
  const origin = env.KH_PILOT_ALLOWED_ORIGIN;
  const db = env.KH_PILOT_DATABASE_URL;
  const uploadDir = env.KH_PILOT_UPLOAD_DIR;
  if (!secret || secret.length < 32 || !origin || !db || !uploadDir) {
    throw new Error('Private pilot requires a 32+ character access token, allowed origin, dedicated local database, and upload directory');
  }
  const url = new URL(db);
  if (!['postgres:', 'postgresql:'].includes(url.protocol) ||
      !['127.0.0.1', 'localhost', '::1', '[::1]'].includes(url.hostname) ||
      !url.pathname || url.pathname === '/') {
    throw new Error('Private pilot database must be a named, local PostgreSQL database');
  }
  const allowedOrigin = new URL(origin);
  if (!['http:', 'https:'].includes(allowedOrigin.protocol) ||
      !['127.0.0.1', 'localhost', '::1', '[::1]'].includes(allowedOrigin.hostname) ||
      allowedOrigin.origin !== origin) {
    throw new Error('Private pilot browser origin must be an exact localhost origin');
  }
  if (!path.isAbsolute(uploadDir) || path.resolve(uploadDir) === path.resolve(defaultUploadsDir)) {
    throw new Error('Private pilot uploads require a separate absolute directory');
  }
  return { secret, origin, db, uploadDir: path.resolve(uploadDir) };
}

function addPilotAccess(app, config) {
  if (!config) return;

  const sessions = new Map();
  const attempts = new Map();
  const secureCookie = config.origin.startsWith('https:');
  const cookieSettings = `HttpOnly; SameSite=Strict; Path=/; Max-Age=${SESSION_MS / 1000}${secureCookie ? '; Secure' : ''}`;
  const cleanCookie = 'HttpOnly; SameSite=Strict; Path=/; Max-Age=0';

  function sameSecret(value) {
    if (typeof value !== 'string') return false;
    const a = crypto.createHash('sha256').update(value).digest();
    const b = crypto.createHash('sha256').update(config.secret).digest();
    return crypto.timingSafeEqual(a, b);
  }

  // Origin check also applies to login/logout. A cross-origin request must not
  // be able to mutate a session, even if credentials accompany it.
  app.use((req, res, next) => {
    res.set('Cache-Control', 'no-store');
    if (req.get('Origin') && req.get('Origin') !== config.origin) {
      return res.status(403).json({ error: 'Origin not allowed' });
    }
    if (!['GET', 'HEAD', 'OPTIONS'].includes(req.method) && req.get('Origin') !== config.origin) {
      return res.status(403).json({ error: 'Pilot mutations require the configured browser origin' });
    }
    next();
  });

  app.get('/api/pilot/status', (req, res) => {
    const token = readSessionCookie(req);
    res.json({ pilot: true, authenticated: sessions.has(token) && sessions.get(token) > Date.now() });
  });

  app.post('/api/pilot/login', (req, res) => {
    const key = req.ip;
    const now = Date.now();
    const bucket = attempts.get(key);
    if (bucket && bucket.start + LOGIN_WINDOW_MS > now && bucket.failures >= 5) {
      return res.status(429).json({ error: 'Too many login attempts' });
    }
    if (!sameSecret(req.body && req.body.accessToken)) {
      const active = bucket && bucket.start + LOGIN_WINDOW_MS > now
        ? bucket : { start: now, failures: 0 };
      active.failures += 1;
      attempts.set(key, active);
      return res.status(401).json({ error: 'Invalid access token' });
    }
    attempts.delete(key);
    const token = crypto.randomBytes(32).toString('hex');
    sessions.set(token, now + SESSION_MS);
    res.set('Set-Cookie', `${COOKIE_NAME}=${token}; ${cookieSettings}`);
    res.json({ authenticated: true });
  });

  app.post('/api/pilot/logout', (req, res) => {
    sessions.delete(readSessionCookie(req));
    res.set('Set-Cookie', `${COOKIE_NAME}=; ${cleanCookie}`);
    res.json({ authenticated: false });
  });

  app.use(['/api/recordings', '/uploads'], (req, res, next) => {
    const token = readSessionCookie(req);
    const expiresAt = sessions.get(token);
    if (!expiresAt || expiresAt <= Date.now()) {
      sessions.delete(token);
      return res.status(401).json({ error: 'Owner pilot login required' });
    }
    next();
  });
}

function readSessionCookie(req) {
  const cookie = (req.headers.cookie || '').split(';').map(s => s.trim())
    .find(s => s.startsWith(`${COOKIE_NAME}=`));
  return cookie ? cookie.slice(COOKIE_NAME.length + 1) : '';
}

module.exports = { readPilotConfig, addPilotAccess };
