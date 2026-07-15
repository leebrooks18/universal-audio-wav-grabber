// api/login.js
export default function handler(req, res) {
  try {
    if (req.method !== 'GET') {
      res.statusCode = 405;
      res.end('Method Not Allowed');
      return;
    }

    const clientId = process.env.SPOTIFY_CLIENT_ID;
    if (!clientId) {
      res.statusCode = 500;
      res.end('Missing SPOTIFY_CLIENT_ID');
      return;
    }

    // Build redirect URI dynamically. If running locally, set PUBLIC_URL or VERCEL_URL.
    const host = process.env.VERCEL_URL || process.env.PUBLIC_URL || 'localhost:3000';
    const redirectUri = `https://${host.replace(/^https?:\/\//, '')}/api/callback`;

    const scopes = [
      'playlist-read-private',
      'playlist-read-collaborative',
      'user-library-read'
    ].join(' ');

    const state = Math.random().toString(36).slice(2);

    // Set state cookie (HttpOnly, Secure in production)
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    const sameSite = '; SameSite=Lax';
    const cookie = `spotify_auth_state=${state}; HttpOnly; Path=/; Max-Age=600${secure}${sameSite}`;

    res.setHeader('Set-Cookie', cookie);

    const params = new URLSearchParams({
      client_id: clientId,
      response_type: 'code',
      redirect_uri: redirectUri,
      scope: scopes,
      state
    });

    res.writeHead(302, { Location: `https://accounts.spotify.com/authorize?${params.toString()}` });
    res.end();
  } catch (err) {
    console.error('login error', err);
    res.statusCode = 500;
    res.end('Internal Server Error');
  }
}
