// Gestionnaire de podcast — serveur local sans dépendance (Node.js >= 18)
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = Number(process.env.PORT) || 3000;
const HOST = process.env.HOST || '127.0.0.1';
const ROOT = __dirname;
const PUBLIC_DIR = path.join(ROOT, 'public');
const DATA_DIR = process.env.DATA_DIR || path.join(ROOT, 'data');
const UPLOAD_DIR = path.join(DATA_DIR, 'uploads');
const DB_FILE = path.join(DATA_DIR, 'db.json');

const COLLECTIONS = ['episodes', 'guests', 'tasks'];

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.mp3': 'audio/mpeg',
  '.m4a': 'audio/mp4',
  '.wav': 'audio/wav',
  '.ogg': 'audio/ogg',
  '.flac': 'audio/flac',
  '.aac': 'audio/aac',
  '.mp4': 'video/mp4',
  '.pdf': 'application/pdf',
  '.txt': 'text/plain; charset=utf-8',
};

// ---------- Stockage JSON ----------

function emptyDb() {
  return {
    settings: {
      title: 'Mon podcast',
      author: '',
      email: '',
      description: '',
      language: 'fr',
      category: 'Society & Culture',
      explicit: false,
      website: '',
      cover: '',
      publicUrl: `http://localhost:${PORT}`,
    },
    episodes: [],
    guests: [],
    tasks: [],
  };
}

fs.mkdirSync(UPLOAD_DIR, { recursive: true });

let db;
try {
  db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
  const base = emptyDb();
  db.settings = { ...base.settings, ...(db.settings || {}) };
  for (const c of COLLECTIONS) if (!Array.isArray(db[c])) db[c] = [];
} catch (e) {
  if (e.code !== 'ENOENT') {
    console.error(`Impossible de lire ${DB_FILE} : ${e.message}`);
    process.exit(1);
  }
  db = emptyDb();
  save();
}

function save() {
  const tmp = DB_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(db, null, 2));
  fs.renameSync(tmp, DB_FILE);
}

const newId = () => crypto.randomUUID();
const now = () => new Date().toISOString();

// ---------- Utilitaires HTTP ----------

function send(res, status, body, headers = {}) {
  const isBuf = Buffer.isBuffer(body);
  const payload = isBuf || typeof body === 'string' ? body : JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': isBuf || typeof body === 'string' ? 'text/plain; charset=utf-8' : 'application/json; charset=utf-8',
    ...headers,
  });
  res.end(payload);
}

function readJson(req, limit = 20 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > limit) {
        reject(Object.assign(new Error('Requête trop volumineuse'), { status: 413 }));
        req.destroy();
      } else chunks.push(c);
    });
    req.on('end', () => {
      if (!chunks.length) return resolve({});
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
      } catch {
        reject(Object.assign(new Error('JSON invalide'), { status: 400 }));
      }
    });
    req.on('error', reject);
  });
}

function serveFile(req, res, file) {
  fs.stat(file, (err, stat) => {
    if (err || !stat.isFile()) return send(res, 404, 'Introuvable');
    const type = MIME[path.extname(file).toLowerCase()] || 'application/octet-stream';
    const range = req.headers.range && /^bytes=(\d*)-(\d*)$/.exec(req.headers.range);
    if (range && (range[1] || range[2])) {
      let start = range[1] ? Number(range[1]) : stat.size - Number(range[2]);
      let end = range[1] && range[2] ? Number(range[2]) : stat.size - 1;
      start = Math.max(0, start);
      end = Math.min(end, stat.size - 1);
      if (start > end) {
        res.writeHead(416, { 'Content-Range': `bytes */${stat.size}` });
        return res.end();
      }
      res.writeHead(206, {
        'Content-Type': type,
        'Content-Length': end - start + 1,
        'Content-Range': `bytes ${start}-${end}/${stat.size}`,
        'Accept-Ranges': 'bytes',
      });
      return fs.createReadStream(file, { start, end }).pipe(res);
    }
    res.writeHead(200, { 'Content-Type': type, 'Content-Length': stat.size, 'Accept-Ranges': 'bytes' });
    if (req.method === 'HEAD') return res.end();
    fs.createReadStream(file).pipe(res);
  });
}

// Résout un chemin à l'intérieur d'un dossier, sans possibilité d'en sortir
function safeJoin(dir, rel) {
  const p = path.normalize(path.join(dir, decodeURIComponent(rel)));
  return p.startsWith(dir + path.sep) ? p : null;
}

function sanitizeName(name) {
  const ext = path.extname(name).toLowerCase().replace(/[^.a-z0-9]/g, '').slice(0, 10);
  const base = path
    .basename(name, path.extname(name))
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-zA-Z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || 'fichier';
  return `${Date.now()}-${base}${ext}`;
}

// ---------- Flux RSS ----------

const xml = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

function fmtDuration(sec) {
  sec = Math.round(Number(sec) || 0);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return [h, m, s].map((n) => String(n).padStart(2, '0')).join(':');
}

function fileUrl(base, rel) {
  if (!rel) return '';
  if (/^https?:\/\//i.test(rel)) return rel;
  return base.replace(/\/+$/, '') + '/' + rel.replace(/^\/+/, '');
}

function buildRss() {
  const s = db.settings;
  const base = s.publicUrl || `http://localhost:${PORT}`;
  const items = db.episodes
    .filter((e) => e.status === 'publie' && e.audio)
    .sort((a, b) => String(b.publishDate || '').localeCompare(String(a.publishDate || '')))
    .map((e) => {
      let length = 0;
      const local = !/^https?:\/\//i.test(e.audio) && safeJoin(DATA_DIR, e.audio);
      if (local) {
        try { length = fs.statSync(local).size; } catch {}
      }
      const ext = path.extname(e.audio).toLowerCase();
      return `    <item>
      <title>${xml(e.title)}</title>
      <description>${xml(e.description)}</description>
      <guid isPermaLink="false">${xml(e.id)}</guid>
      <pubDate>${new Date(e.publishDate || e.createdAt).toUTCString()}</pubDate>
      <enclosure url="${xml(fileUrl(base, e.audio))}" length="${length}" type="${MIME[ext] || 'audio/mpeg'}"/>
      <itunes:duration>${fmtDuration(e.duration)}</itunes:duration>${e.season ? `\n      <itunes:season>${xml(e.season)}</itunes:season>` : ''}${e.number ? `\n      <itunes:episode>${xml(e.number)}</itunes:episode>` : ''}
      <itunes:explicit>${s.explicit ? 'true' : 'false'}</itunes:explicit>${e.cover ? `\n      <itunes:image href="${xml(fileUrl(base, e.cover))}"/>` : ''}
    </item>`;
    })
    .join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>${xml(s.title)}</title>
    <link>${xml(s.website || base)}</link>
    <description>${xml(s.description)}</description>
    <language>${xml(s.language)}</language>
    <itunes:author>${xml(s.author)}</itunes:author>
    <itunes:owner><itunes:name>${xml(s.author)}</itunes:name><itunes:email>${xml(s.email)}</itunes:email></itunes:owner>
    <itunes:category text="${xml(s.category)}"/>
    <itunes:explicit>${s.explicit ? 'true' : 'false'}</itunes:explicit>${s.cover ? `\n    <itunes:image href="${xml(fileUrl(base, s.cover))}"/>` : ''}
${items}
  </channel>
</rss>
`;
}

// ---------- API ----------

async function handleApi(req, res, parts) {
  const [resource, id] = parts;

  if (resource === 'settings') {
    if (req.method === 'GET') return send(res, 200, db.settings);
    if (req.method === 'PUT') {
      const body = await readJson(req);
      db.settings = { ...db.settings, ...body };
      save();
      return send(res, 200, db.settings);
    }
  }

  if (resource === 'export' && req.method === 'GET') {
    return send(res, 200, db, {
      'Content-Disposition': `attachment; filename="podcast-sauvegarde-${new Date().toISOString().slice(0, 10)}.json"`,
    });
  }

  if (resource === 'import' && req.method === 'POST') {
    const body = await readJson(req);
    if (!body || typeof body !== 'object' || !COLLECTIONS.every((c) => Array.isArray(body[c] ?? []))) {
      return send(res, 400, { error: 'Fichier de sauvegarde invalide' });
    }
    const fresh = emptyDb();
    db = { settings: { ...fresh.settings, ...(body.settings || {}) } };
    for (const c of COLLECTIONS) db[c] = body[c] || [];
    save();
    return send(res, 200, { ok: true });
  }

  if (resource === 'upload' && req.method === 'POST') {
    const original = decodeURIComponent(req.headers['x-filename'] || 'fichier');
    const name = sanitizeName(original);
    const dest = path.join(UPLOAD_DIR, name);
    const out = fs.createWriteStream(dest);
    req.pipe(out);
    await new Promise((resolve, reject) => {
      out.on('finish', resolve);
      out.on('error', reject);
      req.on('error', reject);
    });
    const size = fs.statSync(dest).size;
    return send(res, 201, { path: `uploads/${name}`, name: original, size });
  }

  if (COLLECTIONS.includes(resource)) {
    const list = db[resource];
    if (!id) {
      if (req.method === 'GET') return send(res, 200, list);
      if (req.method === 'POST') {
        const body = await readJson(req);
        const item = { ...body, id: newId(), createdAt: now(), updatedAt: now() };
        list.push(item);
        save();
        return send(res, 201, item);
      }
    } else {
      const idx = list.findIndex((x) => x.id === id);
      if (idx === -1) return send(res, 404, { error: 'Élément introuvable' });
      if (req.method === 'GET') return send(res, 200, list[idx]);
      if (req.method === 'PUT') {
        const body = await readJson(req);
        list[idx] = { ...list[idx], ...body, id, updatedAt: now() };
        save();
        return send(res, 200, list[idx]);
      }
      if (req.method === 'DELETE') {
        const [removed] = list.splice(idx, 1);
        // Nettoyage des références à un invité supprimé
        if (resource === 'guests') {
          for (const e of db.episodes) {
            if (Array.isArray(e.guestIds)) e.guestIds = e.guestIds.filter((g) => g !== id);
          }
        }
        if (resource === 'episodes') {
          db.tasks = db.tasks.filter((t) => t.episodeId !== id);
        }
        save();
        return send(res, 200, removed);
      }
    }
  }

  return send(res, 404, { error: 'Route inconnue' });
}

// ---------- Serveur ----------

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const pathname = url.pathname;

    if (pathname.startsWith('/api/')) {
      return await handleApi(req, res, pathname.slice(5).split('/').filter(Boolean));
    }
    if (pathname === '/rss.xml' || pathname === '/feed') {
      return send(res, 200, buildRss(), { 'Content-Type': 'application/rss+xml; charset=utf-8' });
    }
    if (pathname.startsWith('/uploads/')) {
      const file = safeJoin(UPLOAD_DIR, pathname.slice('/uploads/'.length));
      return file ? serveFile(req, res, file) : send(res, 403, 'Interdit');
    }
    const rel = pathname === '/' ? 'index.html' : pathname.slice(1);
    const file = safeJoin(PUBLIC_DIR, rel);
    return file ? serveFile(req, res, file) : send(res, 403, 'Interdit');
  } catch (e) {
    console.error(e);
    if (!res.headersSent) send(res, e.status || 500, { error: e.message || 'Erreur serveur' });
    else res.end();
  }
});

server.listen(PORT, HOST, () => {
  console.log(`\n🎙️  Gestionnaire de podcast lancé : http://localhost:${PORT}`);
  console.log(`   Données : ${DB_FILE}`);
  console.log(`   Flux RSS : http://localhost:${PORT}/rss.xml\n`);
});
