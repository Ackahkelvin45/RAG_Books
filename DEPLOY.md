# Deploying Shepherd Guide

One server runs everything: Postgres, MinIO (book files), the API with the web app, the ingestion
worker, a nightly backup, and Caddy for HTTPS. Only ports 80 and 443 are open.

**Server:** Ubuntu 22.04/24.04, **8 GB RAM** (the two search models take ~3 GB in memory), 2+ CPUs,
40 GB disk. Docker Engine + Compose plugin installed (`curl -fsSL https://get.docker.com | sh`).
**DNS:** an A record for your domain (e.g. `guide.firstlovechurch.org`) pointing at the server.

## 1. First deployment

```bash
# get the code onto the server: git clone if the project is in a repository, otherwise copy it
git clone <repo> shepherd && cd shepherd
#   or, from the Mac:  rsync -a --exclude .venv --exclude node_modules --exclude .env --exclude '131-dagbooks*' \
#                      --exclude ragflow --exclude llama_index --exclude RAG_Book_QA_System ./ <server>:~/shepherd/
cp .env.production.example .env
nano .env                                   # fill every value; secrets: openssl rand -hex 32
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f api   # wait for "Application startup complete"
```

The first start downloads the two models (~4.5 GB) into the `models` volume; the API and worker
share it, and it never downloads again. Caddy fetches the HTTPS certificate automatically once DNS resolves.

Then open `https://<your domain>/admin`, sign in with `ADMIN_PASSWORD`, and either upload books or
bring the library across from the development machine (next section).

### Using your own nginx instead of Caddy

If the server already runs nginx (or you prefer it), start the stack without Caddy and let nginx proxy to the API
on `127.0.0.1:8010`:
```bash
docker compose -f docker-compose.prod.yml -f docker-compose.nginx.yml up -d --build
sudo cp infra/nginx.conf /etc/nginx/sites-available/shepherd    # edit server_name
sudo ln -s /etc/nginx/sites-available/shepherd /etc/nginx/sites-enabled/
sudo certbot --nginx -d guide.example.org && sudo nginx -s reload
```
`infra/nginx.conf` already has the two settings that matter: `proxy_buffering off` (answers stream) and a long
`proxy_read_timeout`. Use the same two compose files for every later `up`.

## 2. Moving the library from the development machine

The dev Mac already holds 131 processed books (passages, embeddings, generated questions). Copying
takes minutes; re-processing on the server would take hours of CPU.

On the Mac (the MinIO container ships its own `mc`, which is simpler than a separate client on Docker Desktop):
```bash
docker exec rag_sheperd-postgres-1 pg_dump -U postgres --data-only -t sources -t chunks shepherd | gzip > library.sql.gz
docker exec rag_sheperd-minio-1 sh -c 'mc alias set local http://localhost:9000 minio minio12345 && mc mirror --quiet local/shepherd-books /tmp/books'
docker cp rag_sheperd-minio-1:/tmp/books ./books
scp library.sql.gz <server>:~/shepherd/ && scp -r books <server>:~/shepherd/
```

On the server (the stack must be up, so the schema exists):
```bash
cd ~/shepherd
gunzip -c library.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -q shepherd
docker compose -f docker-compose.prod.yml cp books minio:/tmp/books
docker compose -f docker-compose.prod.yml exec minio sh -c "mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD && mc mb -p local/shepherd-books; mc mirror --quiet /tmp/books local/shepherd-books"
```
Tested end to end 2026-09-20: 131 books / 13,843 passages restore in about a minute; the book files are ~130 MB.
Users, conversations and logs are not copied: the pilot starts clean. Create the first accounts by
signing up in the app, then promote pastors and shepherds to `leader` in `/admin/users`.

## 3. Updating

```bash
git pull            # or the same rsync as in step 1
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
