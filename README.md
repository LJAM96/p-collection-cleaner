# P Collection Cleanup Tool


A Python script that removes collections from your Plex server that don't have any labels, while keeping all labeled collections intact.

## Features

- ✅ Connects to any Plex server using URL and token
- ✅ Scans all libraries for collections
- ✅ Removes only collections without labels
- ✅ Preserves all collections that have labels
- ✅ Dry-run mode for safe testing
- ✅ Detailed logging and confirmation prompts
- ✅ Error handling and recovery
- ✅ **Docker support with environment variables**
- ✅ **Enhanced debugging and troubleshooting output**

## Quick Start

### Option 1: Docker (Recommended)

1. **Create environment file:**
```bash
cp .env.example .env

# Edit .env with your Plex server details


```

2. **Run dry-run to test (scheduled service):**
```bash
docker-compose up p-collection-cleaner



```

3. **Execute cleanup immediately (after confirming dry-run results):**




```bash
docker-compose run --rm -e PLEX_RUN_ONCE=true -e PLEX_DRY_RUN=false p-collection-cleaner





```

### Option 2: Local Python

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run script:**
```bash
python p-collection-cleaner.py --server-url http://your-server:32400 --token YOUR_TOKEN



```

## Docker Usage (Detailed)

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PLEX_URL` | Plex server URL | - | ✅ |

| `PLEX_TOKEN` | Plex authentication token | - | ✅ |

| `PLEX_DRY_RUN` | Set to `false` to execute | `true` | ❌ |

| `PLEX_NO_CONFIRM` | Skip confirmation prompts | `false` | ❌ |
| `PLEX_DEBUG` | Enable debug logging | `false` | ❌ |

### Docker Examples

**Basic dry-run:**
```bash
docker run -e PLEX_URL=http://host.docker.internal:32400 -e PLEX_TOKEN=xyz123 p-collection-cleaner
```

**Execute with debug output:**
```bash
docker run -e PLEX_URL=http://192.168.1.100:32400 \
           -e PLEX_TOKEN=xyz123 \
           -e PLEX_DRY_RUN=false \
           -e PLEX_DEBUG=true \
           p-collection-cleaner
```

**Additional docker-compose commands:**
```bash
# Dry run with debug logging
docker-compose run --rm -e PLEX_RUN_ONCE=true -e PLEX_DEBUG=true p-collection-cleaner

# Execute without confirmation
docker-compose run --rm -e PLEX_RUN_ONCE=true -e PLEX_DRY_RUN=false -e PLEX_NO_CONFIRM=true p-collection-cleaner
```

### Building the Docker Image

```bash
# Build locally
docker build -t p-collection-cleaner .

# Or use docker-compose
docker-compose build

## Continuous Integration

The repository includes a GitHub Actions workflow (`.github/workflows/docker-build.yml`) that builds a multi-platform Docker image on pushes to the `main` branch, pull requests, or manual `workflow_dispatch` runs. This job uses Docker Buildx to create images that support both `linux/amd64` and `linux/arm64` architectures, validating that the container builds successfully on a variety of devices.
```

## Local Python Usage

### Getting Your Plex Token

You'll need your Plex authentication token. You can find it by:
1. Going to a web browser and opening a Plex media item
2. Opening browser developer tools (F12)
3. Looking for the `X-Plex-Token` in network requests

Or visit: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### Command Line Usage

**Environment Variables (Recommended):**
```bash
export PLEX_URL=http://localhost:32400
export PLEX_TOKEN=your_token_here
python p-collection-cleaner.py
```

**Command Line Arguments:**
```bash
python p-collection-cleaner.py --server-url http://localhost:32400 --token YOUR_TOKEN
```

### Command Line Options

- `--server-url`: Plex server URL (or use `PLEX_URL` env var)
- `--token`: Plex authentication token (or use `PLEX_TOKEN` env var)
- `--dry-run`: Show what would be removed without removing
- `--execute`: Actually remove collections (overrides dry-run and `PLEX_DRY_RUN`)
- `--no-confirm`: Skip confirmation prompts
- `--debug`: Enable debug logging

### Local Python Examples

```bash
# Dry run with debug logging
python p-collection-cleaner.py --server-url http://localhost:32400 --token abc123 --debug

# Execute without confirmation prompts
python p-collection-cleaner.py --server-url http://localhost:32400 --token abc123 --execute --no-confirm

# Using environment variables
export PLEX_URL=http://localhost:32400
export PLEX_TOKEN=abc123
export PLEX_DEBUG=true
python p-collection-cleaner.py
```

## How It Works

1. **Connection**: Connects to your Plex server using the provided URL and token
2. **Library Scanning**: Iterates through all libraries on your server
3. **Collection Analysis**: For each library, examines all collections
4. **Label Checking**: Checks if each collection has any labels assigned
5. **Safe Removal**: Removes only collections that have zero labels
6. **Preservation**: Keeps all collections that have one or more labels

## Safety Features

- **Dry Run Default**: The script runs in dry-run mode by default
- **Confirmation Prompts**: Asks for confirmation before removing collections from each library
- **Detailed Logging**: Shows exactly what collections will be/were removed
- **Error Handling**: Gracefully handles connection issues and API errors
- **Preserves Labeled Collections**: Never touches collections that have labels

## Enhanced Debugging & Troubleshooting

The script provides detailed output to help with debugging and understanding what's happening:

### Connection Debugging
```
==================================================
PLEX CONNECTION ATTEMPT
==================================================
Server URL: http://localhost:32400
Token length: 32 characters
Token preview: abcd1234...xyz9
Attempting to connect to Plex server...
✓ Successfully connected to Plex server!
Server Name: MyPlexServer
Server Version: 1.40.1.8227
Server Platform: Linux
Authenticated as: myusername
Connection verification complete!
```

### Collection Analysis Output
```
📚 Analyzing library: Movies
Library type: movie
✓ Found 12 total collections in library 'Movies'

🔍 Analyzing each collection:
----------------------------------------
❌ [1] 'Auto Collection 1' (25 items) - NO LABELS → MARKED FOR REMOVAL
✅ [2] 'My Favorites' (15 items) - HAS LABELS: ['favorite', 'personal'] → KEEPING
❌ [3] 'Unwanted Collection' (8 items) - NO LABELS → MARKED FOR REMOVAL
----------------------------------------
📊 Summary for 'Movies':
   Total collections: 12
   Labeled collections: 9
   Unlabeled collections: 3
```

### Final Summary
```
============================================================
🔍 DRY RUN COMPLETE - SUMMARY
============================================================
Libraries processed: 4
Total collections found: 45
Collections that would be removed: 8
Collections that would remain: 37

💡 To actually remove collections, run with --execute flag
============================================================
```

### Error Troubleshooting

If you encounter connection issues, the script provides detailed error information:

```
==================================================
PLEX CONNECTION FAILED
==================================================
PlexAPI Error: 401 Unauthorized
Error Type: PlexApiException

Troubleshooting Tips:
1. Verify server URL is correct and reachable
2. Check if Plex server is running
3. Verify authentication token is valid
4. Ensure network connectivity to Plex server
5. 401 Unauthorized - Check your Plex token
```

## Requirements

- **Docker** (recommended) OR Python 3.11+
- PlexAPI library (automatically installed in Docker)
- Valid Plex server access
- Plex authentication token

## Docker Network Configuration

### Local Plex Server (Same Machine)
Use `host.docker.internal:32400` in Docker:
```bash
PLEX_URL=http://host.docker.internal:32400
```

### Remote Plex Server
Use the actual IP address:
```bash
PLEX_URL=http://192.168.1.100:32400
```

### Docker Compose with Host Network
The provided `docker-compose.yml` uses `network_mode: "host"` for easy access to local services.

## Files Created

- `p-collection-cleaner.py` - Main Python script
- `requirements.txt` - Python dependencies
- `Dockerfile` - Docker container configuration
- `docker-compose.yml` - Docker Compose configuration for scheduled and one-off runs
- `.env.example` - Environment variable template
- `README.md` - This documentation

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.






