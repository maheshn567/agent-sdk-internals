import http from 'http';
import { corsair } from "./corsair.js";

async function authenticate() {
  const clientId = process.env.GMAIL_CLIENT_ID;
  const clientSecret = process.env.GMAIL_CLIENT_SECRET;
  
  if (!clientId || !clientSecret) {
    console.error("Error: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in your .env file.");
    return;
  }
  
  const port = 51234;
  const redirectUri = `http://localhost:${port}/oauth/callback`;
  const scopes = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
  ];
  
  const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${encodeURIComponent(clientId)}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&response_type=code` +
    `&scope=${encodeURIComponent(scopes.join(" "))}` +
    `&access_type=offline` +
    `&prompt=consent`;
    
  // Start local server to listen for the redirect callback
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url || '', `http://${req.headers.host}`);
    
    if (url.pathname === '/oauth/callback') {
      const code = url.searchParams.get('code');
      
      if (code) {
        // Send success page to browser
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(`
          <html>
            <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px; background: #f4f7f6; color: #333;">
              <h1 style="color: #2e7d32;">Authentication Successful!</h1>
              <p>You can close this tab and return to your terminal.</p>
            </body>
          </html>
        `);
        
        console.log("\nReceived authorization code. Exchanging for tokens...");
        
        // Shut down server
        server.close();
        
        try {
          const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
              code: code,
              client_id: clientId,
              client_secret: clientSecret,
              redirect_uri: redirectUri,
              grant_type: "authorization_code"
            })
          });
          
          if (!tokenResponse.ok) {
            const errorText = await tokenResponse.text();
            throw new Error(`Token exchange failed: ${tokenResponse.status} - ${errorText}`);
          }
          
          const tokenData = await tokenResponse.json() as {
            access_token: string;
            refresh_token: string;
            expires_in: number;
          };
          
          console.log("Saving tokens to Corsair database...");
          const client = corsair;
          await client.gmail.keys.set_access_token(tokenData.access_token);
          if (tokenData.refresh_token) {
            await client.gmail.keys.set_refresh_token(tokenData.refresh_token);
          }
          await client.gmail.keys.set_expires_at(
            String(Math.floor(Date.now() / 1000) + tokenData.expires_in)
          );
          
          console.log("Success! You are now fully authenticated to Gmail!");
          process.exit(0);
        } catch (err: any) {
          console.error("\nAuthentication failed during token exchange:", err.message);
          process.exit(1);
        }
      } else {
        res.writeHead(400, { 'Content-Type': 'text/plain' });
        res.end('Missing code parameter.');
        server.close();
        process.exit(1);
      }
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not found');
    }
  });
  
  server.listen(port, () => {
    console.log("\n==================================================");
    console.log("1. Add the following Redirect URI to your Google Console Credentials:");
    console.log(redirectUri);
    console.log("\n2. Click/Open the following URL to log in:");
    console.log(authUrl);
    console.log("==================================================\n");
    console.log("Waiting for browser redirect...");
  });
}

authenticate();
