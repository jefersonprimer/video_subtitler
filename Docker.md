# Running the Video Subtitler Application with Docker

## Introduction

Docker is a platform that allows you to develop, ship, and run applications in isolated environments called containers. Containers are lightweight, standalone, and executable packages that include everything needed to run a piece of software, including the code, runtime, system tools, system libraries, and settings. For this video subtitler application, Docker provides a consistent and reproducible environment, ensuring that the application runs the same way regardless of the underlying infrastructure. This eliminates the "it works on my machine" problem and simplifies setup for developers and users.

## Prerequisites

Before you can run the video subtitler application with Docker, you need to have Docker Desktop installed on your machine. Docker Desktop is available for Windows, macOS, and Linux. You can download and install it from the official Docker website: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

Once installed, make sure Docker Desktop is running.

## Building the Docker Image

The first step is to build a Docker image from the `Dockerfile` provided in the project. This image will contain everything needed to run the video subtitler application, including the Python environment, dependencies, and application code.

1.  **Open your terminal or command prompt.**
2.  **Navigate to the project's root directory.** This is the directory where the `Dockerfile` is located.
3.  **Run the following command:**
```
bash
    docker build -t video-subtitler-app .
    
```
**Explanation of the command:**

    *   `docker build`: This is the command used to build a Docker image.
    *   `-t video-subtitler-app`: This option tags the image with the name `video-subtitler-app`. You can choose any name you prefer, but `video-subtitler-app` is a descriptive choice for this project.
    *   `.`: This specifies the build context. The `.` means that Docker should use the current directory as the build context. Docker will look for the `Dockerfile` in this directory.

    This command will read the instructions in the `Dockerfile`, create an image and it will be tagged with the name that you chose.

## Running the Docker Container

After successfully building the Docker image, you can run a container based on this image.

1.  **Ensure Docker Desktop is running.**
2.  **Open your terminal or command prompt.**
3.  **Run the following command:**
```
bash
    docker run -p 8000:8000 video-subtitler-app
    
```
**Explanation of the command:**

    *   `docker run`: This is the command to start a new container.
    *   `-p 8000:8000`: This option publishes (or maps) a port. It maps port 8000 on your host machine to port 8000 inside the container. This is necessary because the application inside the container is running on port 8000, and this mapping allows you to access it from your host machine.
    *   `video-subtitler-app`: This is the name of the image you built in the previous step. Docker will use this image to create and run the container.

    This command will run a container with the application, and the port 8000 will be exposed.

## Access the Application

Once the container is running, you can access the video subtitler application in your web browser by navigating to:
```
http://localhost:8000
```
Your application is now live and running inside a docker container.

## Conclusion

Using Docker to run the video subtitler application provides several advantages:

*   **Consistency:** The application runs in the same environment regardless of the host machine.
*   **Isolation:** The application and its dependencies are isolated from other applications on the host machine.
*   **Simplicity:** Setting up and running the application is simplified to a few commands.

Now that you have your project running on Docker, consider exploring more advanced Docker features, such as Docker Compose for managing multi-container applications, Docker Swarm or Kubernetes for container orchestration, and Docker Hub for sharing your images.