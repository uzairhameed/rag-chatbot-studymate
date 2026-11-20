# StudyMate

StudyMate is a multimodal study assistant. It lets users create study rooms, share rooms with other accounts, upload supported learning materials, and ask questions grounded in those materials.

## Features

- User registration and login with bearer-token authentication
- Owner-managed study rooms, including adding members and deleting rooms
- File uploads for PDF, DOCX, CSV, TXT, Markdown, PPTX, common image formats, audio formats, and video formats
- Text extraction, chunking, embeddings, and room-scoped vector search
- Chat history with source filenames, file types, chunk indexes, and excerpts
- S3 object storage for uploaded files

Video questions currently use the video's audio transcript. The app does not describe visual content from video frames.

## Architecture

- **Streamlit frontend:** `frontend/streamlit_app.py`, with screens under `frontend/screens/` and reusable UI components under `frontend/components/`
- **FastAPI backend:** `app/main.py`, with authentication, rooms, uploads, and chat routers
- **PostgreSQL:** user accounts, rooms, memberships, uploaded-file records, and chat messages
- **Qdrant:** local persistent vector storage under `qdrant_storage/`
- **Amazon S3:** uploaded source files
- **Groq:** language and multimodal model requests used by ingestion and chat

## Requirements

- Python and pip
- PostgreSQL running locally or reachable through `DATABASE_URL`
- An AWS account, region, bucket, and credentials with access to the bucket
- A Groq API key

## Local setup

Run these commands from the project root in Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set values for your environment:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/courselens
SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GROQ_API_KEY=your-groq-api-key
AWS_REGION=your-aws-region
S3_BUCKET_NAME=your-s3-bucket
```

Create the PostgreSQL database named in `DATABASE_URL` before applying migrations. Run migrations from the project root:

```bash
alembic upgrade head
```

Configure AWS credentials through your local AWS CLI profile or another supported boto3 credential source. Do not commit `.env` or real credentials.

## Run locally

Start the FastAPI backend in one Git Bash terminal:

```bash
source .venv/Scripts/activate
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

Start the Streamlit frontend in a second terminal from the project root:

```bash
source .venv/Scripts/activate
streamlit run frontend/streamlit_app.py
```

The frontend API client currently targets `http://127.0.0.1:8000`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Secret used to sign JWT access tokens |
| `ALGORITHM` | JWT signing algorithm; defaults to `HS256` in the backend |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime in minutes; defaults to `30` |
| `GROQ_API_KEY` | Groq API credential |
| `AWS_REGION` | AWS region containing the S3 bucket |
| `S3_BUCKET_NAME` | Bucket used for uploaded source files |

## Data and storage notes

- `.env` is excluded by `.gitignore`; keep real credentials out of source control.
- Qdrant uses local disk storage in `qdrant_storage/`. Keep this directory on persistent storage when deploying.
- Uploaded files live in S3; the PostgreSQL `uploaded_files` records keep their room and storage-key metadata.
- Deleting a room also deletes its database records, S3 objects, and Qdrant vectors.

## API overview

- `/auth/register` and `/auth/login` — account registration and login
- `/rooms/` — list and create rooms
- `/rooms/{room_id}` — owner-only room deletion
- `/rooms/{room_id}/members` — owner-only member addition
- `/upload/{room_id}` — list or upload room files
- `/chat/{room_id}` — ask a question and receive sources
- `/chat/{room_id}/history` — read or clear room history

Use `/docs` on the running API for request and response schemas.
