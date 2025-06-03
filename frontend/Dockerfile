# Stage 1: Build the React app
FROM node:18-alpine as builder
# Using Node 18-alpine as a common, reasonably up-to-date, and small base image.
# The original subtask mentioned 16-alpine. 18-alpine is also a good choice.

WORKDIR /app

# Copy package.json and yarn.lock (or package-lock.json if using npm)
# This allows Docker to cache dependencies unless these files change.
COPY package.json yarn.lock ./
# If using npm instead of yarn:
# COPY package.json package-lock.json ./

# Install dependencies
# Using yarn install --frozen-lockfile for yarn to ensure reproducible builds.
RUN yarn install --frozen-lockfile
# Or if using npm:
# RUN npm ci

# Copy the rest of the application code
COPY . .

# Set REACT_APP_API_BASE_URL at build time if it's known and static.
# Otherwise, it can be configured at runtime via Nginx environment substitution (more complex)
# or by having Nginx proxy requests. For simplicity, we assume it might be baked in or
# handled by Nginx proxying.
# ARG REACT_APP_API_BASE_URL=/api/v1
# ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL

# Build the React application for production
RUN yarn build
# Or if using npm:
# RUN npm run build

# Stage 2: Serve the static files with Nginx
FROM nginx:1.23-alpine
# Using a recent stable version of Nginx on Alpine for small size.

# Copy the build output from the builder stage to Nginx's html directory
COPY --from=builder /app/build /usr/share/nginx/html

# Optional: Copy custom Nginx configuration for client-side routing (React Router)
# This ensures that direct navigation to routes like /market are handled by index.html.
COPY nginx.conf /etc/nginx/conf.d/default.conf
# If nginx.conf is not provided, Nginx will use its default configuration.

# Expose port 80 (standard HTTP port Nginx listens on)
EXPOSE 80

# Command to run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
