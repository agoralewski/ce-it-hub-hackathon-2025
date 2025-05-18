# Static Files Troubleshooting Guide

If you're experiencing issues with static files (CSS, JS, images) not loading properly in your KSP application, follow this troubleshooting guide.

## Common Issues and Solutions

### 1. Static files not being served by Nginx

**Symptoms:**
- CSS styles are missing
- JavaScript functionality is broken
- Images don't appear
- Browser console shows 404 errors for static files

**Solutions:**

a) **Run the rebuild script:**
```bash
./rebuild_static.sh
```
This script will:
- Stop all containers
- Clean the staticfiles directory
- Rebuild and restart containers
- Run the collectstatic command

b) **Check Nginx logs:**
```bash
docker compose logs nginx
```
Look for 404 errors or other issues related to static files.

c) **Check file paths:**
```bash
# List all files in the staticfiles directory
ls -la ./staticfiles
```
Ensure that your CSS files are properly collected.

### 2. Static files collected but with wrong permissions

**Symptoms:**
- Files exist in the staticfiles directory but still can't be accessed

**Solutions:**
```bash
# Fix permissions on staticfiles directory
chmod -R 755 ./staticfiles
chmod -R 755 ./media

# Restart containers
docker compose restart
```

### 3. Django not finding static files

**Symptoms:**
- Static files work in development but not in Docker

**Solutions:**
1. Check your Django settings:
   - `STATIC_URL` should be `'static/'`
   - `STATIC_ROOT` should be `BASE_DIR / 'staticfiles'`
   - `STATICFILES_DIRS` should include `BASE_DIR / 'static'`

2. Run collectstatic manually:
```bash
docker compose exec web uv run manage.py collectstatic --noinput --clear
```

### 4. Browser caching issues

**Symptoms:**
- Changes to CSS/JS are not reflected after updates

**Solutions:**
1. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)
2. Clear browser cache
3. Add version query parameter to CSS links in templates:
```html
<link rel="stylesheet" href="{% static 'css/style.css' %}?v={% now 'U' %}">
```

## Docker Container Structure

For reference, here's how the static files are mapped in the Docker setup:

- **Web container:**
  - `/app/static`: Source static files
  - `/app/staticfiles`: Collected static files (destination of collectstatic)

- **Nginx container:**
  - `/app/static`: Mapped from host's ./static
  - `/app/staticfiles`: Mapped from host's ./staticfiles
  - `/app/media`: Mapped from host's ./media

## Manual Verification

To manually verify static files are correctly collected:

```bash
# Enter the web container
docker compose exec web sh

# Check if static files exist
ls -la /app/staticfiles

# Check permissions
ls -la /app/static
```

For Nginx:
```bash
# Enter the nginx container
docker compose exec nginx sh

# Check if static files are accessible
ls -la /app/staticfiles
ls -la /app/static
```

If you still experience issues after following this guide, check the application logs for more detailed error messages.
