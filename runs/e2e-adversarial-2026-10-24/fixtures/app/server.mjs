import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';

const html = new URL('./page.html', import.meta.url);
createServer(async (_req, res) => {
  try {
    const body = await readFile(html, 'utf8');
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
    res.end(body);
  } catch (error) {
    res.writeHead(500, { 'content-type': 'text/plain' });
    res.end(String(error));
  }
}).listen(4173, '127.0.0.1', () => console.log('pilot app listening on 4173'));
