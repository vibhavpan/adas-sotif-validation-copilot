FROM --platform=linux/amd64 python:3.10-slim

RUN apt-get update && apt-get install -y libfontconfig1 && rm -rf /var/lib/apt-get/lists/*

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libgl1 \
    libglu1-mesa \
    libx11-6 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# Download the official Linux demo package from latest GitHub release
RUN wget https://github.com/esmini/esmini/releases/latest/download/esmini-demo_Linux.zip \
    && unzip esmini-demo_Linux.zip \
    && rm esmini-demo_Linux.zip \
    && mv esmini* esmini

WORKDIR /opt/esmini

ENTRYPOINT ["./bin/esmini"]
