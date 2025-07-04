# Google OAuth Setup Guide for OwnChat

This guide will help you set up Google OAuth for the OwnChat application.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" or select an existing project
3. Give your project a name (e.g., "OwnChat")
4. Click "Create"

## Step 2: Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Identity" and enable it
3. Alternatively, you can enable "Google+ API" (legacy but still works)

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" (unless you have a Google Workspace account)
3. Fill in the required information:
   - App name: OwnChat
   - User support email: Your email
   - Developer contact information: Your email
4. Click "Save and Continue"
5. Skip "Scopes" for now (click "Save and Continue")
6. Add test users (your Gmail address) in the "Test users" section
7. Click "Save and Continue"

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Name: OwnChat
5. Add Authorized JavaScript origins:
   - `http://localhost:3000`
   - `http://127.0.0.1:3000`
6. Add Authorized redirect URIs:
   - `http://localhost:3000`
   - `http://127.0.0.1:3000`
7. Click "Create"

## Step 5: Copy Credentials

After creating the OAuth client, you'll see a popup with:
- Client ID (starts with something like `123456789-abc...googleusercontent.com`)
- Client Secret (shorter string)

## Step 6: Update Environment Files

### Backend (.env)
```bash
GOOGLE_CLIENT_ID=your-client-id-from-step-5
GOOGLE_CLIENT_SECRET=your-client-secret-from-step-5
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id-from-step-5
```

## Step 7: Test the Integration

1. Start both backend and frontend servers
2. Go to the login page (`http://localhost:3000/login`)
3. You should see a "Continue with Google" button
4. Click it to test the Google OAuth flow

## Troubleshooting

### Common Issues:

1. **"This app isn't verified" warning:**
   - This is normal for development
   - Click "Advanced" → "Go to OwnChat (unsafe)" to proceed

2. **Invalid redirect URI:**
   - Make sure your URLs in Google Console match exactly: `http://localhost:3000`
   - Check that you're accessing the app via the same URL

3. **Client ID not found:**
   - Verify the Client ID is correctly copied to both `.env` files
   - Make sure there are no extra spaces or quotes

4. **CORS errors:**
   - Ensure the backend CORS_ORIGINS includes `http://localhost:3000`

### Testing with Different Emails:

During development, you can only use email addresses you've added as "test users" in the OAuth consent screen configuration.

## Production Deployment

For production:
1. Update the OAuth consent screen with your production domain
2. Add your production URLs to authorized origins and redirect URIs
3. Submit your app for verification if needed (for more than 100 users)
4. Update environment variables with production URLs