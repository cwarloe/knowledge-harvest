const fs = require('fs');
const os = require('os');
const path = require('path');
const request = require('supertest');

jest.mock('pg', () => ({
  Pool: jest.fn().mockImplementation(() => ({ query: jest.fn().mockResolvedValue({ rows: [] }) }))
}));

const uploads = fs.mkdtempSync(path.join(os.tmpdir(), 'kh-pilot-test-'));
const origin = 'http://localhost:3000';
const secret = 'owner-private-pilot-synthetic-only-strong-access-token';

process.env.KH_PRIVATE_PILOT = '1';
process.env.KH_PILOT_ALLOWED_ORIGIN = origin;
process.env.KH_PILOT_ACCESS_TOKEN = secret;
process.env.KH_PILOT_DATABASE_URL = 'postgres://pilot:local@127.0.0.1:5432/kh_pilot_test';
process.env.KH_PILOT_UPLOAD_DIR = uploads;

const app = require('../server');

afterAll(() => {
  fs.rmSync(uploads, { recursive: true, force: true });
  for (const key of ['KH_PRIVATE_PILOT', 'KH_PILOT_ALLOWED_ORIGIN',
    'KH_PILOT_ACCESS_TOKEN', 'KH_PILOT_DATABASE_URL', 'KH_PILOT_UPLOAD_DIR']) {
    delete process.env[key];
  }
});

describe('opt-in local private pilot', () => {
  beforeAll(() => {
    fs.writeFileSync(path.join(uploads, 'synthetic.webm'), Buffer.from('synthetic test clip'));
  });

  it('denies every recording and raw-file path without a session', async () => {
    const responses = await Promise.all([
      request(app).get('/api/recordings'),
      request(app).get('/api/recordings/123'),
      request(app).post('/api/recordings').set('Origin', origin)
        .attach('video', Buffer.from('data'), 'clip.webm'),
      request(app).delete('/api/recordings/123').set('Origin', origin),
      request(app).get('/uploads/synthetic.webm'),
      request(app).head('/uploads/synthetic.webm')
    ]);
    responses.forEach(response => expect(response.status).toBe(401));
    expect(fs.readdirSync(uploads)).toEqual(['synthetic.webm']);
  });

  it('refuses invalid tokens, cross-origin login, and missing-origin mutations', async () => {
    expect((await request(app).post('/api/pilot/login').set('Origin', origin)
      .send({ accessToken: 'wrong' })).status).toBe(401);
    expect((await request(app).post('/api/pilot/login').set('Origin', 'https://attacker.invalid')
      .send({ accessToken: secret })).status).toBe(403);
    expect((await request(app).post('/api/pilot/login')
      .send({ accessToken: secret })).status).toBe(403);
  });

  it('allows an authenticated owner and revokes the session on logout', async () => {
    const agent = request.agent(app);
    const login = await agent.post('/api/pilot/login').set('Origin', origin)
      .send({ accessToken: secret });
    expect(login.status).toBe(200);
    expect(login.headers['set-cookie'][0]).toMatch(/HttpOnly; SameSite=Strict/);
    expect((await agent.get('/api/pilot/status')).body.authenticated).toBe(true);
    expect((await agent.get('/api/recordings')).status).toBe(200);
    const video = await agent.get('/uploads/synthetic.webm');
    expect(video.status).toBe(200);
    expect(video.body.toString()).toBe('synthetic test clip');
    expect((await agent.get('/api/recordings').set('Origin', 'https://attacker.invalid')).status).toBe(403);
    expect((await agent.post('/api/pilot/logout').set('Origin', origin)).status).toBe(200);
    expect((await agent.get('/uploads/synthetic.webm')).status).toBe(401);
  });

  it('rejects unsafe pilot configuration instead of falling back to public settings', () => {
    const { readPilotConfig } = require('../pilotAccess');
    const base = { KH_PRIVATE_PILOT: '1', KH_PILOT_ACCESS_TOKEN: secret,
      KH_PILOT_ALLOWED_ORIGIN: origin,
      KH_PILOT_DATABASE_URL: 'postgres://pilot@127.0.0.1:5432/kh_pilot_test',
      KH_PILOT_UPLOAD_DIR: uploads };
    expect(() => readPilotConfig({ ...base, KH_PILOT_ACCESS_TOKEN: 'short' }, '/tmp/default')).toThrow();
    expect(() => readPilotConfig({ ...base, KH_PRIVATE_PILOT: 'true' }, '/tmp/default')).toThrow();
    expect(() => readPilotConfig({ ...base, KH_PILOT_DATABASE_URL: 'postgres://prod.example.com/customer' }, '/tmp/default')).toThrow();
    expect(() => readPilotConfig({ ...base, KH_PILOT_UPLOAD_DIR: '/tmp/default' }, '/tmp/default')).toThrow();
    expect(() => readPilotConfig({ ...base, KH_PILOT_ALLOWED_ORIGIN: 'https://public.example.com' }, '/tmp/default')).toThrow();
  });
});
