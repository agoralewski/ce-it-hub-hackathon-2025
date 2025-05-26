FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom config
COPY nginx.conf /etc/nginx/conf.d/

# Set permissions
RUN chmod 644 /etc/nginx/conf.d/nginx.conf
