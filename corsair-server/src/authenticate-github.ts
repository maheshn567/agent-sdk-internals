import http from 'http';
import { corsair } from "./corsair.js";

async function authenticate() {
  const clientId = process.env.GITHUB_CLIENT_ID;
  const clientSecret = process.env.GITHUB_CLIENT_SECRET;
  
  if (!clientId || !clientSecret) {
    console.error("Error: GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in your .env file.");
    return;
  }
  
  const port = 51234;
  const redirectUri = `http://localhost:${port}/oauth/callback`;
  const scopes = ["repo", "read:org", "user"];
  
  const authUrl = `https://github.com/login/oauth/authorize?` +
    `client_id=${encodeURIComponent(clientId)}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&scope=${encodeURIComponent(scopes.join(" "))}` +
    `&state=github-oauth-state-123`;
    
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
              <h1 style="color: #2e7d32;">GitHub Authentication Successful!</h1>
              <p>You can close this tab and return to your terminal.</p>
            </body>
          </html>
        `);
        
        console.log("\nReceived authorization code. Exchanging for tokens...");
        
        // Shut down server
        server.close();
        
        try {
          const tokenResponse = await fetch("https://github.com/login/oauth/access_token", {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
              "Accept": "application/json"
            },
            body: new URLSearchParams({
              code: code,
              client_id: clientId,
              client_secret: clientSecret,
              redirect_uri: redirectUri
            })
          });
          
          if (!tokenResponse.ok) {
            const errorText = await tokenResponse.text();
            throw new Error(`Token exchange failed: ${tokenResponse.status} - ${errorText}`);
          }
          
          const tokenData = await tokenResponse.json() as {
            access_token: string;
            refresh_token?: string;
            expires_in?: number;
            scope: string;
          };
          
          console.log("Saving tokens to Corsair database...");
          const client = corsair;
          await client.github.keys.set_access_token(tokenData.access_token);
          if (tokenData.refresh_token) {
            await client.github.keys.set_refresh_token(tokenData.refresh_token);
          }
          
          console.log("Success! You are now fully authenticated to GitHub!");
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
    console.log("1. Add the following Redirect URI to your GitHub OAuth App Settings:");
    console.log(redirectUri);
    console.log("\n2. Click/Open the following URL to log in:");
    console.log(authUrl);
    console.log("==================================================\n");
    console.log("Waiting for browser redirect...");
  });
}

authenticate();
