# Adaptive Learning Secure Sandbox Image
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install minimal compilers and runtimes for Python, C++, and Java
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-minimal \
    g++ \
    gcc \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Create a non-privileged sandbox user
RUN useradd -m -u 10001 -s /bin/bash sandboxuser

# Working directory
WORKDIR /sandbox
RUN chown -R sandboxuser:sandboxuser /sandbox

USER sandboxuser
