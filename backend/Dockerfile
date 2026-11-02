# Use Miniconda official image
FROM anaconda/miniconda@sha256:38939b55a6cdca3b5cb24eb8dd9f7f7bcf49cd4ec9e6d72760f8161b906f9085

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Create a secure, non-root user
RUN useradd -m -s /bin/bash -u 1001 appuser

# Switch directory
WORKDIR /home/appuser

# Copy dependency file
COPY conda-lock.yml .

# Accept conda TOS and create environment with dependencies
ENV CONDA_PLUGINS_AUTO_ACCEPT_TOS=true
RUN conda create --file conda-lock.yml --name thematic_back --quiet && \
    conda config --set default_activation_env thematic_back

# Copy rest of the files
COPY . .

# Give ownership of database to 1001 user
RUN chown -R 1001:1001 ./database
RUN chown -R 1001:1001 ./config

# Switch to low-privileged user
USER 1001

# Expose port and start API
EXPOSE 8000
CMD ["conda","run","-n","thematic_back","uvicorn","main:app","--host","0.0.0.0","--port","8000"]