# Everything the analysis can use, in one image: Python, git, tokei (line counts) and gitleaks (secrets).
# The analyzed repository is mounted read-only; reports go to a separate volume.
FROM python:3.12-slim

ARG TOKEI_VERSION=12.1.2
ARG GITLEAKS_VERSION=8.21.2

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && curl -fsSL "https://github.com/XAMPPRocky/tokei/releases/download/v${TOKEI_VERSION}/tokei-x86_64-unknown-linux-gnu.tar.gz" | tar -xz -C /usr/local/bin tokei \
 && curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" | tar -xz -C /usr/local/bin gitleaks \
 && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
 && git config --system --add safe.directory '*'

WORKDIR /opt/software-archaeology
COPY pyproject.toml README.md archaeology.example.yaml ./
COPY archaeology ./archaeology
COPY specs ./specs
COPY schemas ./schemas
COPY prompts ./prompts
RUN pip install --no-cache-dir ".[anthropic]"

RUN useradd --create-home archaeologist
USER archaeologist
WORKDIR /work
ENTRYPOINT ["archaeology"]
CMD ["--help"]
