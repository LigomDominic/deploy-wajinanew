# Render.com Deployment Guide

This guide will help you deploy the Wajina Suite application to Render.com.

## Prerequisites

1. A GitHub account
2. A Render.com account (sign up at https://render.com)
3. Your project pushed to a GitHub repository

## Step 1: Prepare Your Repository

1. Make sure all your code is committed and pushed to GitHub
2. Ensure the following files are in your repository:
   - `app.py` - Main Flask application
   - `requirements.txt` - Python dependencies
   - `Procfile` - Process file for Render
   - `gunicorn_config.py` - Gunicorn configuration
   - `render.yaml` - Render blueprint (optional, for one-click deployment)
   - `runtime.txt` - Python version specification
   - `init_db.py` - Database initialization script

## Step 2: Deploy Using Render Blueprint (Recommended)

### Option A: One-Click Deployment with render.yaml

1. Go to https://dashboard.render.com
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create:
   - A web service
   - A PostgreSQL database
   - All necessary environment variables

### Option B: Manual Deployment

1. **Create PostgreSQL Database:**
   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Choose a name (e.g., `wajina-suite-db`)
   - Select the free plan
   - Note the Internal Database URL

2. **Create Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name:** `wajina-suite`
     - **Environment:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt && python init_db.py`
     - **Start Command:** `gunicorn --config gunicorn_config.py app:app`
     - **Plan:** Free (or choose a paid plan)

3. **Set Environment Variables:**
   - In your web service settings, go to "Environment"
   - Add the following variables:
     ```
     SECRET_KEY=<generate-a-random-secret-key>
     FLASK_ENV=production
     DATABASE_URL=<from-postgres-database-internal-url>
     MAIL_SERVER=smtp.gmail.com
     MAIL_PORT=587
     MAIL_USE_TLS=true
     MAIL_USERNAME=<your-email>
     MAIL_PASSWORD=<your-app-password>
     FLUTTERWAVE_ENVIRONMENT=sandbox
     ```
   - For `SECRET_KEY`, you can generate one using:
     ```python
     import secrets
     print(secrets.token_hex(32))
     ```

4. **Link Database to Web Service:**
   - In your web service settings, go to "Environment"
   - Click "Link Database" and select your PostgreSQL database
   - Render will automatically set the `DATABASE_URL` variable

## Step 3: Configure Email (Optional)

If you want to enable email functionality:

1. For Gmail:
   - Enable 2-factor authentication
   - Generate an App Password: https://myaccount.google.com/apppasswords
   - Use the app password in `MAIL_PASSWORD`

2. Add email environment variables in Render dashboard

## Step 4: Configure Payment Gateway (Optional)

If you want to enable Flutterwave payments:

1. Sign up at https://flutterwave.com
2. Get your API keys from the dashboard
3. Add the keys as environment variables in Render

## Step 5: Deploy

1. Click "Create Web Service" or "Apply" (for Blueprint)
2. Render will:
   - Install dependencies
   - Initialize the database
   - Start your application
3. Wait for deployment to complete (usually 2-5 minutes)

## Step 6: Access Your Application

1. Once deployed, Render will provide a URL like: `https://wajina-suite.onrender.com`
2. Visit the URL in your browser
3. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `admin123`
4. **IMPORTANT:** Change the admin password immediately after first login!

## Troubleshooting

### Database Connection Issues

- Ensure `DATABASE_URL` is set correctly
- Check that the database is linked to your web service
- Verify PostgreSQL is running

### Build Failures

- Check build logs in Render dashboard
- Ensure all dependencies in `requirements.txt` are correct
- Verify Python version in `runtime.txt` matches Render's supported versions

### Application Errors

- Check application logs in Render dashboard
- Verify all environment variables are set
- Ensure database initialization completed successfully

### Static Files Not Loading

- Render handles static files automatically
- Ensure your `static/` folder is in the repository
- Check file paths in your templates

## Important Notes

1. **Free Tier Limitations:**
   - Services spin down after 15 minutes of inactivity
   - First request after spin-down may take 30-60 seconds
   - Consider upgrading to a paid plan for production

2. **File Storage:**
   - Uploaded files are stored in the filesystem
   - Files are lost when the service restarts (on free tier)
   - Consider using cloud storage (AWS S3, Cloudinary) for production

3. **Database:**
   - Free PostgreSQL databases are deleted after 90 days of inactivity
   - Upgrade to a paid plan for persistent databases

4. **Security:**
   - Always use strong `SECRET_KEY` in production
   - Change default admin password immediately
   - Use environment variables for sensitive data
   - Enable HTTPS (automatic on Render)

## Support

For issues specific to:
- **Render:** Check Render documentation or support
- **Application:** Check application logs in Render dashboard
- **Database:** Verify database connection and credentials

## Next Steps

1. Set up custom domain (optional)
2. Configure email notifications
3. Set up payment gateway
4. Configure automated backups
5. Set up monitoring and alerts

