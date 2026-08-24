FROM debian:bookworm-slim AS production

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
       latexmk \
       texlive-fonts-recommended \
       texlive-lang-spanish \
       texlive-latex-base \
       texlive-latex-recommended \
       texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
ENTRYPOINT ["latexmk"]
