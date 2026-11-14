# ZERO Config Server – laeuft auf jedem Host, der Docker nimmt (Render, Koyeb, Railway, Fly.io, eigener VPS).
# Kein Build noetig: nur Python-Standardbibliothek.
FROM python:3.12-slim

WORKDIR /app
COPY zero_config_server.py /app/

# Configs bleiben hier erhalten (Host-Volume dranhaengen, wenn sie Neustarts ueberleben sollen)
ENV DATA=/app/data
RUN mkdir -p /app/data

# Die meisten Hoster setzen $PORT selbst; Standard 8787 fuer lokal/VPS
ENV PORT=8787
EXPOSE 8787

CMD ["python", "-I", "zero_config_server.py"]
