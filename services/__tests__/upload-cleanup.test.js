const fs = require('fs');
const path = require('path');
const request = require('supertest');
const app = require('../server');

const uploadsDir = path.join(__dirname, '..', 'uploads');
const listRecordings = () =>
  fs.readdirSync(uploadsDir).filter((f) => f.startsWith('recording-'));

// Wait briefly for the async cleanup to finish.
const settle = () => new Promise((resolve) => setTimeout(resolve, 100));

describe('POST /api/recordings cleanup', () => {
  it('rejects a video without a title and does not keep the uploaded file', async () => {
    const before = listRecordings();
    const res = await request(app)
      .post('/api/recordings')
      .attach('video', Buffer.from('not really a video'), 'clip.webm');
    expect(res.status).toBe(400);
    await settle();
    expect(listRecordings()).toEqual(before);
  });

  it('rejects a request with neither title nor video', async () => {
    const res = await request(app).post('/api/recordings').field('title', '');
    expect(res.status).toBe(400);
  });
});
