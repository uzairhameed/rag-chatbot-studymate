# StudyMate

StudyMate is a multimodal study assistant for the education technology (EdTech) industry. Students, tutors, and study groups can upload learning materials to shared rooms, ask questions grounded in those materials, and review answers with source references.

## Problem statement

Study materials are often spread across PDFs, slides, notes, spreadsheets, images, and recordings. Finding a specific explanation across those files takes time. StudyMate brings the materials into one room and uses retrieval-augmented generation (RAG) to find relevant passages before generating an answer.

## Features

- User registration and login with bearer-token authentication
- Study rooms with owner-managed membership and deletion
- Uploads for PDF, DOCX, CSV, TXT, Markdown, PPTX, common image formats, audio formats, and video formats
- Text extraction, chunking, embeddings, reranking, and room-scoped vector search
- Chat history with source filenames, file types, chunk indexes, and excerpts
- Uploaded-file storage in Amazon S3

For regular questions, StudyMate retrieves and reranks relevant chunks. Full-document summary requests use all chunks from the selected document as answer context. Video questions currently use the video's audio transcript; the app does not describe visual content from video frames.

## Architecture

- **Streamlit frontend:** `frontend/streamlit_app.py`, with screens in `frontend/screens/` and reusable UI components in `frontend/components/`.
- **FastAPI backend:** `app/main.py`, with authentication, rooms, uploads, and chat routers in `app/routers/`.
- **PostgreSQL:** stores users, rooms, room memberships, uploaded-file records, and chat messages.
- **Qdrant:** stores chunk embeddings and metadata. Local development uses persistent storage under `qdrant_storage/`; Docker Compose runs Qdrant as a separate service with a persistent volume.
- **Amazon S3:** stores uploaded source files. Locally, boto3 uses the configured AWS credential chain. On EC2, the instance role provides S3 access.
- **Groq:** provides language and multimodal model requests used by ingestion and chat.

## Requirements

- Python 3.11 and pip
- PostgreSQL
- An AWS S3 bucket and region
- A Groq API key
- Docker Engine and Docker Compose for the EC2 deployment

For local AWS access, configure the AWS CLI profile or another boto3 credential source. On EC2, attach an instance role with the required S3 permissions; do not put AWS access keys in the app's `.env` file.

## Local setup

Run these commands from the project root in Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with values for your local environment:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/studymate_db
SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GROQ_API_KEY=your-groq-api-key
AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-s3-bucket
```

Create the PostgreSQL database named in `DATABASE_URL` before applying migrations. From the project root, run:

```bash
alembic upgrade head
```

Keep `.env` and real credentials out of source control.

## Run locally

Start FastAPI in one Git Bash terminal:

```bash
source .venv/Scripts/activate
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Swagger UI is available at `http://127.0.0.1:8000/docs`.

Start Streamlit in a second terminal from the project root:

```bash
source .venv/Scripts/activate
streamlit run frontend/streamlit_app.py
```

The local frontend API client targets `http://127.0.0.1:8000`.

## Quick demo

1. Start PostgreSQL, configure `.env`, and run `alembic upgrade head`.
2. Start FastAPI and Streamlit using the commands above.
3. Register an account and sign in.
4. Create a study room and upload a supported file.
5. Ask a question that can be answered from the uploaded material.
6. Review the answer's sources and open the room's chat history.
7. If signed in as the room owner, try adding a member or deleting a room.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string for local development. Docker Compose overrides it for the API container. |
| `SECRET_KEY` | Secret used to sign JWT access tokens. |
| `ALGORITHM` | JWT signing algorithm; the backend defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime in minutes; the backend defaults to `30`. |
| `GROQ_API_KEY` | Groq API credential. |
| `AWS_REGION` | AWS region containing the S3 bucket. |
| `S3_BUCKET_NAME` | Bucket used for uploaded source files. |
| `POSTGRES_DB` | Database name used by the PostgreSQL Compose service. |
| `POSTGRES_USER` | Database user used by the PostgreSQL Compose service. |
| `POSTGRES_PASSWORD` | Database password used by the PostgreSQL Compose service. |

For the EC2 Compose deployment, put the `POSTGRES_*` values in the root `.env` alongside the application variables. Protect that file with `chmod 600`. Do not commit it.

## Docker deployment on AWS EC2

The EC2 deployment uses Docker Compose to run FastAPI, Streamlit, PostgreSQL, and Qdrant in separate containers. Nginx accepts HTTP traffic on port 80 and proxies requests to the frontend and API. The API and frontend ports bind to `127.0.0.1`; PostgreSQL and Qdrant use persistent Docker volumes. Uploaded files are stored in S3.

The current `docker-compose.ec2.yml` references the `1.1` API and frontend images on Docker Hub.

### Start the EC2 deployment

Create the root `.env` file on EC2 with the environment variables above, including `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. The EC2 instance role supplies AWS credentials to boto3.

From the project directory:

```bash
sudo docker compose -f docker-compose.ec2.yml up -d
sudo docker compose -f docker-compose.ec2.yml ps
sudo docker compose -f docker-compose.ec2.yml logs --tail=60 api frontend
```

The API container runs database migrations at startup.

### Nginx and network access

The working Nginx configuration is tracked at `deploy/nginx/studymate.conf`. Install it on EC2 with:

```bash
sudo cp deploy/nginx/studymate.conf /etc/nginx/sites-available/studymate
sudo ln -sfn /etc/nginx/sites-available/studymate /etc/nginx/sites-enabled/studymate
sudo nginx -t
sudo systemctl reload nginx
```

Nginx routes `/` to Streamlit and `/api/`, `/docs`, `/redoc`, and `/openapi.json` to FastAPI.

Allow inbound SSH (TCP 22) only from your IP and HTTP (TCP 80) through the EC2 security group. Do not expose ports 8000, 8501, 5432, or 6333 publicly. The current deployment uses HTTP; HTTPS has not been configured.

### Deploy updated images

For a new release, build and push new API and frontend image tags from the development computer, update the tags in `docker-compose.ec2.yml`, then commit and push the Compose change. On EC2, update the repository and recreate the app services:

```bash
git pull origin main
sudo docker compose -f docker-compose.ec2.yml pull api frontend
sudo docker compose -f docker-compose.ec2.yml up -d api frontend
sudo docker compose -f docker-compose.ec2.yml ps
sudo docker compose -f docker-compose.ec2.yml logs --tail=60 api frontend
```

After deployment, test the website and `/docs` through the EC2 public address.

The API image is large, so check available EC2 disk space before pulling a release. Removing an old API container and image can cause temporary API downtime, but does not remove PostgreSQL or Qdrant volumes. Do not run `docker compose down -v` unless intentionally deleting persistent database and vector data.

## Data and storage notes

- `.env` is excluded by `.gitignore`; keep real credentials out of source control and Docker images.
- Qdrant data is persistent: locally under `qdrant_storage/`, and in Docker Compose in the `qdrant_data` volume.
- Uploaded files live in S3; PostgreSQL `uploaded_files` records retain room and storage-key metadata.
- Deleting a room removes its database records, S3 objects, and Qdrant vectors.

## API overview

- `/auth/register` and `/auth/login` — account registration and login
- `/rooms/` — list and create rooms
- `/rooms/{room_id}` — owner-only room deletion
- `/rooms/{room_id}/members` — owner-only member addition
- `/upload/{room_id}` — list or upload room files
- `/chat/{room_id}` — ask a question and receive sources
- `/chat/{room_id}/history` — read or clear room history

Use `/docs` on the running API for request and response schemas.