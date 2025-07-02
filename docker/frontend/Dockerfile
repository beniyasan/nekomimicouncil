FROM node:18-alpine

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
RUN npm install

# Copy application code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["npm", "run", "dev"]