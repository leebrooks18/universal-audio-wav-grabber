// api/callback.js

function parseCookies(cookieHeader = '') {
  return cookieHeader.split(';').map(c => c.trim()).reduce((acc, pair) => {
    if (!pair) return acc;
    const idx = pair.indexOf('=');
    const k = pair.substring(0, idx);
    const v = pair.substring(idx + 1);
    acc[k] = decodeURIComponent(v);
    return acc;
  }, {});
}

export default async function handler(req, res) {
  try {
    if (req.method !== 'GET') {
      res.statusCode = 405;
      res.end('Method Not Allowed');
      return;
    }

    const { code, state: returnedState } = req.query || {};
    if (!code) {
      res.statusCode = 400;
      res.end('Missing code');
      return;
    }

    // Validate state cookie
    const cookies = parseCookies(req.headers?.cookie || '');
    const savedState = cookies['spotify_auth_state'];
    if (!savedState || savedState !== returnedState) {
      res.statusCode = 400;
      res.end('Invalid state');
      return;
    }

    const clientId = process.env.SPOTIFY_CLIENT_ID;
    const clientSecret = process.env.SPOTIFY_CLIENT_SECRET;
    if (!clientId || !clientSecret) {
      res.statusCode = 500;
      res.end('Missing Spotify credentials');
      return;
    }

    const host = process.env.VERCEL_URL || process.env.PUBLIC_URL || 'localhost:3000';
    const redirectUri = `https://${host.replace(/^https?:\/\//, '')}/api/callback`;

    const tokenUrl = 'https://accounts.spotify.com/api/token';
    const bodyParams = new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: redirectUri
    });

    const authHeader = 'Basic ' + Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

    // Use global fetch when available (Node 18+). Fallback to dynamic import of node-fetch only if necessary.
    const fetchImpl = (typeof globalThis.fetch === 'function') ? globalThis.fetch : (await import('node-fetch').then(m => m.default));

    const tokenRes = await fetchImpl(tokenUrl, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: bodyParams.toString()
    });

    if (!tokenRes.ok) {
      const text = await tokenRes.text();
      console.error('token exchange error', tokenRes.status, text);
      res.statusCode = 502;
      res.end('Token exchange failed');
      return;
    }

    const tokenJson = await tokenRes.json();

    // Save refresh token in a secure cookie (demo). Consider a DB in production.
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    const sameSite = '; SameSite=Lax';
    const cookie = `spotify_refresh=${encodeURIComponent(tokenJson.refresh_token || '')}; HttpOnly; Path=/; Max-Age=2592000${secure}${sameSite}`;

    // Clear the state cookie (expire immediately)
    const clearState = `spotify_auth_state=; HttpOnly; Path=/; Max-Age=0${secure}${sameSite}`;

    res.setHeader('Set-Cookie', [cookie, clearState]);
    // Redirect to a small success page
    res.writeHead(302, { Location: '/auth-success.html' });
    res.end();
  } catch (err) {
    console.error('callback error', err);
    res.statusCode = 500;
    res.end('Internal Server Error');
  }
}
