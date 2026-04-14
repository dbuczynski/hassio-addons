FROM php:8.2-apache

# Install base packages needed for the environment (like jq for JSON parsing)
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Add Index view config to apache
RUN echo "<Directory /var/www/html>\nOptions +Indexes\n</Directory>" > /etc/apache2/conf-available/indexes.conf && a2enconf indexes

# Copy execution script and make it executable
COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 80

CMD [ "/run.sh" ]
