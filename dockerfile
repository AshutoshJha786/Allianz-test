# Start from a base image
FROM node:14

# Declare build arguments
ARG DD_ACCOUNT_ID
ARG DD_CLIENT_TOKEN

# # Set the working directory
# WORKDIR /app

# # Copy package.json and package-lock.json first
# COPY package*.json ./

# # Install dependencies
# RUN npm install

# # Copy the rest of your application code
# COPY . .

# Set environment variables for the build process using ARGs
ENV REACT_APP_DD_ACCOUNT_ID=${DD_ACCOUNT_ID}
ENV REACT_APP_DD_CLIENT_TOKEN=${DD_CLIENT_TOKEN}

# Print the environment variables for debugging
RUN echo "Building with Account ID: ${REACT_APP_DD_ACCOUNT_ID} and Client Token: ${REACT_APP_DD_CLIENT_TOKEN}"

# # Build the application
# RUN npm run build

# # Command to run your application (adjust as necessary)
# CMD ["npm", "start"]
