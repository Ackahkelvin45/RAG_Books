# Deploying Shepherd Guide

One server runs everything: Postgres, MinIO (book files), the API with the web app, the ingestion
worker, a nightly backup, and Caddy for HTTPS. Only ports 80 and 443 are open.

**Server:** Ubuntu 22.04/24.04, **8 GB RAM** (the two search models take ~3 GB in memory), 2+ CPUs,
40 GB disk. Docker Engine + Compose plugin installed (`curl -fsSL https://get.docker.com | sh`).
**DNS:** an A record for your domain (e.g. `guide.firstlovechurch.org`) pointing at the server.

## 1. First deployment

```bash
git clone <repo> shepherd && cd shepherd
cp .env.production.example .env
nano .env                                   # fill every value; secrets: openssl rand -hex 32
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f api   # wait for "Application startup complete"
```

The first start downloads the two models (~4.5 GB) into the `models` volume; the API and worker
share it, and it never downloads again. Caddy fetches the HTTPS certificate automatically once DNS resolves.

Then open `https://<your domain>/admin`, sign in with `ADMIN_PASSWORD`, and either upload books or
bring the library across from the development machine (next section).

## 2. Moving the library from the development machine

The dev Mac already holds 131 processed books (passages, embeddings, generated questions). Copying
takes minutes; re-processing on the server would take hours of CPU.

On the Mac:
```bash
docker exec rag_sheperd-postgres-1 pg_dump -U postgres --data-only \
  -t sources -t chunks shepherd | gzip > library.sql.gz
docker run --rm --network host -v "$PWD:/out" minio/mc sh -c \
  'mc alias set dev http://localhost:9000 minio minio12345 && mc mirror dev/shepherd-books /out/books'
scp library.sql.gz -r books <server>:~/shepherd/
```

On the server:
```bash
cd ~/shepherd
gunzip -c library.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres shepherd
docker run --rm --network shepherd_default -v "$PWD/books:/books" minio/mc sh -c \
  "mc alias set prod http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD && mc mb -p prod/shepherd-books && mc mirror /books prod/shepherd-books"
```
Users, conversations and logs are not copied: the pilot starts clean. Create the first accounts by
signing up in the app, then promote pastors and shepherds to `leader` in `/admin/users`.

## 3. Updating

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build   # rebuilds the image, restarts api + worker, runs new migrations
```

## 4. Backups and restore

The `backup` service writes `shepherd-YYYY-MM-DD.sql.gz` nightly into the `backups` volume and keeps
14 days. Copy them off the server too (e.g. a daily `rsync` or `docker cp`):
```bash
docker compose -f docker-compose.prod.yml cp backup:/backups ./offsite-backups
```

Restore (practise this once before the pilot):
```bash
docker compose -f docker-compose.prod.yml stop api worker
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -c 'drop database shepherd' -c 'create database shepherd'
gunzip -c offsite-backups/shepherd-2026-09-20.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres shepherd
docker compose -f docker-compose.prod.yml start api worker
```
Book files live in the `miniodata` volume; back that up with `docker run --rm -v shepherd_miniodata:/data -v $PWD:/out alpine tar czf /out/minio.tgz /data`.

## 5. Checking it works

```bash
docker compose -f docker-compose.prod.yml ps                 # every service "healthy" / "running"
docker compose -f docker-compose.prod.yml logs --tail 50 worker
docker compose -f docker-compose.prod.yml exec api python -m eval.run retrieval --kind hand   # search sanity check, no cost
```

## 6. Running costs

Server ~$30–50/month. DeepSeek ~$0.001–0.002 per question. Resend free tier covers the pilot's sign-up emails.
