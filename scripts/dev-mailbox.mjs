#!/usr/bin/env node
/**
 * A dev-only "mailbox": a stub of the mail relay the API posts to.
 *
 * The API's real configuration posts verification emails to MAIL_RELAY_URL with
 * a bearer token. For the demo, this tiny server plays that role: it accepts the
 * relay POST, remembers the body per recipient, and answers a plain HTTP GET so
 * the web app can show an "inbox" the partner can see the code arrive in.
 *
 * This is NOT a product surface. It exists so the demo can run the API's real
 * mail path while a human watches the email arrive. Nothing here ships.
 *
 * Usage:
 *   MAILBOX_TOKEN=demo-mailbox node scripts/dev-mailbox.mjs
 *
 * Endpoints:
 *   POST /            bearer MAILBOX_TOKEN, relay body { to, subject, text }
 *   GET  /inbox?email=addr   latest message for addr (dev only, no auth)
 */
import { createServer } from 'node:http';
import { URL } from 'node:url';

const TOKEN = process.env.MAILBOX_TOKEN ?? 'demo-mailbox';
const PORT = Number(process.env.MAILBOX_PORT ?? '4000');
const messages = new Map(); // email -> { subject, text, receivedAt }

const server = createServer((req, res) => {
  const url = new URL(req.url ?? '/', `http://${req.headers.host}`);
  const chunks = [];

  if (req.method === 'POST' && url.pathname === '/') {
    if (req.headers.authorization !== `Bearer ${TOKEN}`) {
      res.writeHead(401).end('unauthorized');
      return;
    }
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      try {
        const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        const email = (body.to ?? '').toLowerCase();
        messages.set(email, { subject: body.subject, text: body.text, receivedAt: new Date() });
        res.writeHead(200).end('queued');
      } catch {
        res.writeHead(400).end('bad payload');
      }
    });
    return;
  }

  if (req.method === 'GET' && url.pathname === '/inbox') {
    const email = (url.searchParams.get('email') ?? '').toLowerCase();
    const message = messages.get(email);
    res.writeHead(200, { 'content-type': 'application/json' });
    if (!message) {
      res.end(JSON.stringify({ email, message: null }));
      return;
    }
    // Peel the token out of the email text for the demo UI, keeping the raw
    // text too so "an email really arrived".
    const token = (message.text.match(/Token:\s*([^\s]+)/) ?? [])[1] ?? null;
    res.end(
      JSON.stringify({
        email,
        token,
        subject: message.subject,
        message: message.text,
        receivedAt: message.receivedAt.toISOString(),
      }),
    );
    return;
  }

  res.writeHead(404).end('not found');
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`dev mailbox listening on http://127.0.0.1:${PORT}`);
});