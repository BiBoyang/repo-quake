import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';

const html = new URL('./page.html', import.meta.url);
let events = [];
let sequence = 0;
const server = createServer(async (req, res) => {
  try {
    if (req.url === '/events' && req.method === 'GET') {
      res.writeHead(200, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
      res.end(JSON.stringify(events));
      return;
    }
    if (req.url === '/reset' && req.method === 'POST') {
      events = [];
      sequence = 0;
      res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
      res.end('[]');
      return;
    }
    if (req.url === '/event' && req.method === 'POST') {
      let body = '';
      for await (const chunk of req) body += chunk;
      const parsed = JSON.parse(body);
      const event = { sequence: ++sequence, at: new Date().toISOString(), ...parsed };
      events.push(event);
      res.writeHead(200, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
      res.end(JSON.stringify(event));
      return;
    }
    const body = await readFile(html, 'utf8');
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
    res.end(body);
  } catch (error) {
    res.writeHead(500, { 'content-type': 'text/plain' });
    res.end(String(error));
  }
});
server.listen(4173, '127.0.0.1', () => console.log('semantic audit app listening on 4173'));
