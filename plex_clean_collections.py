#!/usr/bin/env python3
"""
Plex Collection Cleanup Script

This script connects to a Plex server and removes all collections that don't have labels,
while keeping collections with labels intact.
"""

import argparse
import fnmatch
import logging
import os
import sys
import traceback
from typing import List, Optional

from plexapi.server import PlexServer
from plexapi.library import Library
from plexapi.collection import Collection
from plexapi.exceptions import PlexApiException


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration with enhanced formatting for Docker."""
    level = logging.DEBUG if debug else logging.INFO

    # Enhanced format for better debugging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()  # Clear any existing handlers
    root_logger.addHandler(console_handler)

    # Also configure PlexAPI logger for debugging
    plex_logger = logging.getLogger('plexapi')
    plex_logger.setLevel(logging.DEBUG if debug else logging.WARNING)

    logging.info(f"Logging initialized - Level: {logging.getLevelName(level)}")
    if debug:
        logging.debug("Debug mode enabled - verbose output active")


def parse_label_list(label_string: str) -> List[str]:
    """Parse comma-separated label string into list, filtering empty values."""
    if not label_string:
        return []
    return [label.strip() for label in label_string.split(',') if label.strip()]


def matches_label_pattern(label: str, patterns: List[str]) -> bool:
    """Check if a label matches any of the given patterns (supports wildcards)."""
    if not patterns:
        return False

    for pattern in patterns:
        if fnmatch.fnmatch(label.lower(), pattern.lower()):
            return True
    return False


def should_remove_collection(collection, delete_labels: List[str], delete_patterns: List[str]) -> tuple[bool, str]:
    """
    Determine if a collection should be removed based on label rules.

    Returns:
        tuple: (should_remove: bool, reason: str)
    """
    labels = collection.labels
    label_names = [label.tag for label in labels] if labels else []

    # Rule 1: Always remove collections without any labels
    if not labels:
        return True, "NO LABELS"

    # Rule 2: Remove collections with matching exact labels
    for label_name in label_names:
        if label_name.lower() in [dl.lower() for dl in delete_labels]:
            return True, f"MATCHES DELETE LABEL: {label_name}"

    # Rule 3: Remove collections with labels matching patterns
    for label_name in label_names:
        if matches_label_pattern(label_name, delete_patterns):
            return True, f"MATCHES DELETE PATTERN: {label_name}"

    # Keep collection
    return False, f"HAS PROTECTED LABELS: {label_names}"


def connect_to_plex(server_url: str, token: str) -> PlexServer:
    """Connect to Plex server with enhanced error reporting."""
    logging.info("=" * 50)
    logging.info("PLEX CONNECTION ATTEMPT")
    logging.info("=" * 50)
    logging.info(f"Server URL: {server_url}")
    logging.info(f"Token length: {len(token)} characters")
    logging.info(f"Token preview: {token[:8]}...{token[-4:] if len(token) > 12 else token}")

    try:
        logging.info("Attempting to connect to Plex server...")
        plex = PlexServer(server_url, token)

        # Get detailed server information
        logging.info(f"✓ Successfully connected to Plex server!")
        logging.info(f"Server Name: {plex.friendlyName}")
        logging.info(f"Server Version: {plex.version}")
        logging.info(f"Server Platform: {plex.platform}")
        logging.info(f"Server Platform Version: {plex.platformVersion}")

        # Test basic functionality
        try:
            account = plex.myPlexAccount()
            logging.info(f"Authenticated as: {account.username if account else 'Unknown'}")
        except Exception as e:
            logging.warning(f"Could not get account info: {e}")

        logging.info("Connection verification complete!")
        return plex

    except PlexApiException as e:
        logging.error("=" * 50)
        logging.error("PLEX CONNECTION FAILED")
        logging.error("=" * 50)
        logging.error(f"PlexAPI Error: {e}")
        logging.error(f"Error Type: {type(e).__name__}")

        # Provide troubleshooting information
        logging.error("\nTroubleshooting Tips:")
        logging.error("1. Verify server URL is correct and reachable")
        logging.error("2. Check if Plex server is running")
        logging.error("3. Verify authentication token is valid")
        logging.error("4. Ensure network connectivity to Plex server")

        if "401" in str(e):
            logging.error("5. 401 Unauthorized - Check your Plex token")
        elif "404" in str(e):
            logging.error("5. 404 Not Found - Check your server URL")
        elif "timeout" in str(e).lower():
            logging.error("5. Connection timeout - Check network/firewall")

        sys.exit(1)

    except Exception as e:
        logging.error("=" * 50)
        logging.error("UNEXPECTED CONNECTION ERROR")
        logging.error("=" * 50)
        logging.error(f"Unexpected error: {e}")
        logging.error(f"Error Type: {type(e).__name__}")
        logging.error(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)


def get_collections_for_removal(library: Library, delete_labels: List[str], delete_patterns: List[str]) -> List[Collection]:
    """Get all collections in a library that should be removed based on label rules."""
    collections_to_remove = []

    logging.info(f"\n📚 Analyzing library: {library.title}")
    logging.info(f"Library type: {library.type}")

    try:
        logging.debug("Fetching collections from library...")
        collections = library.collections()
        logging.info(f"✓ Found {len(collections)} total collections in library '{library.title}'")

        if not collections:
            logging.info("No collections found in this library")
            return collections_to_remove

        logging.info("\n🔍 Analyzing each collection:")
        logging.info("-" * 40)

        for i, collection in enumerate(collections, 1):
            try:
                logging.debug(f"[{i}/{len(collections)}] Processing: {collection.title}")

                # Get collection details
                try:
                    item_count = len(collection.items())
                except Exception as e:
                    logging.debug(f"Could not get item count for '{collection.title}': {e}")
                    item_count = "Unknown"

                # Determine if collection should be removed
                should_remove, reason = should_remove_collection(collection, delete_labels, delete_patterns)

                if should_remove:
                    collections_to_remove.append(collection)
                    logging.info(f"❌ [{i}] '{collection.title}' ({item_count} items) - {reason} → MARKED FOR REMOVAL")
                else:
                    logging.info(f"✅ [{i}] '{collection.title}' ({item_count} items) - {reason} → KEEPING")

            except Exception as e:
                logging.error(f"❗ Error checking collection '{collection.title}': {e}")
                logging.debug(f"Full traceback: {traceback.format_exc()}")

        logging.info("-" * 40)
        logging.info(f"📊 Summary for '{library.title}':")
        logging.info(f"   Total collections: {len(collections)}")
        logging.info(f"   Collections to keep: {len(collections) - len(collections_to_remove)}")
        logging.info(f"   Collections to remove: {len(collections_to_remove)}")

    except Exception as e:
        logging.error(f"❗ Error getting collections from library '{library.title}': {e}")
        logging.error(f"Error details: {traceback.format_exc()}")

    return collections_to_remove


def cleanup_collections(plex: PlexServer, dry_run: bool = True, confirm: bool = True,
                       delete_labels: List[str] = None, delete_patterns: List[str] = None) -> None:
    """Clean up collections based on label rules from all libraries."""
    if delete_labels is None:
        delete_labels = []
    if delete_patterns is None:
        delete_patterns = []
    total_removed = 0
    total_collections = 0
    libraries_processed = 0

    logging.info("\n" + "=" * 60)
    logging.info("🚀 STARTING COLLECTION CLEANUP PROCESS")
    logging.info("=" * 60)

    try:
        logging.info("Fetching library information...")
        libraries = plex.library.sections()
        logging.info(f"✓ Found {len(libraries)} libraries on server")

        if not libraries:
            logging.warning("No libraries found on server!")
            return

        logging.info("\n📋 Available libraries:")
        for i, lib in enumerate(libraries, 1):
            logging.info(f"  {i}. {lib.title} ({lib.type})")

        for library in libraries:
            libraries_processed += 1
            logging.info(f"\n{'='*20} LIBRARY {libraries_processed}/{len(libraries)} {'='*20}")

            collections_to_remove = get_collections_for_removal(library, delete_labels, delete_patterns)
            total_collections += len(library.collections()) if hasattr(library, 'collections') else 0

            if not collections_to_remove:
                logging.info(f"✅ No collections to remove found in library '{library.title}' - skipping")
                continue

            logging.info(f"\n⚠️  Found {len(collections_to_remove)} collections to remove:")
            for i, collection in enumerate(collections_to_remove, 1):
                logging.info(f"   {i}. {collection.title}")

            if dry_run:
                logging.info(f"\n🔍 DRY RUN: Would remove {len(collections_to_remove)} collections from '{library.title}'")
                total_removed += len(collections_to_remove)
                continue

            # In execute mode
            if confirm:
                logging.warning(f"\n⚠️  About to PERMANENTLY DELETE {len(collections_to_remove)} collections from '{library.title}'!")
                response = input(f"Proceed with deletion? Type 'DELETE' to confirm: ")
                if response != 'DELETE':
                    logging.info(f"Skipping library '{library.title}' - user cancelled")
                    continue

            logging.info(f"\n🗑️  Removing collections from '{library.title}'...")
            for i, collection in enumerate(collections_to_remove, 1):
                try:
                    logging.info(f"[{i}/{len(collections_to_remove)}] Removing: {collection.title}")
                    collection.delete()
                    total_removed += 1
                    logging.info(f"✓ Successfully removed: {collection.title}")
                except Exception as e:
                    logging.error(f"❌ Failed to remove collection '{collection.title}': {e}")
                    logging.debug(f"Delete error traceback: {traceback.format_exc()}")

    except Exception as e:
        logging.error(f"\n❌ Critical error during cleanup: {e}")
        logging.error(f"Error details: {traceback.format_exc()}")
        sys.exit(1)

    # Final summary
    logging.info("\n" + "=" * 60)
    if dry_run:
        logging.info("🔍 DRY RUN COMPLETE - SUMMARY")
    else:
        logging.info("✅ CLEANUP COMPLETE - SUMMARY")
    logging.info("=" * 60)

    logging.info(f"Libraries processed: {libraries_processed}")
    logging.info(f"Total collections found: {total_collections}")

    if dry_run:
        logging.info(f"Collections that would be removed: {total_removed}")
        logging.info(f"Collections that would remain: {total_collections - total_removed}")
        logging.info("\n💡 To actually remove collections, run with --execute flag")
    else:
        logging.info(f"Collections successfully removed: {total_removed}")
        logging.info(f"Collections remaining: {total_collections - total_removed}")

    logging.info("=" * 60)


def get_env_var(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """Get environment variable with enhanced error reporting."""
    value = os.getenv(name, default)

    if required and not value:
        logging.error(f"❌ Required environment variable '{name}' is not set!")
        logging.error("Available environment variables:")
        for key in sorted(os.environ.keys()):
            if any(term in key.lower() for term in ['plex', 'token', 'url', 'server']):
                logging.error(f"   {key} = {os.environ[key][:10]}..." if len(os.environ[key]) > 10 else f"   {key} = {os.environ[key]}")
        sys.exit(1)

    if value:
        logging.debug(f"Environment variable '{name}' loaded successfully")

    return value


def main():
    """Main function with environment variable support."""
    parser = argparse.ArgumentParser(
        description="Remove Plex collections that don't have labels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  PLEX_URL          Plex server URL (e.g., http://localhost:32400)
  PLEX_TOKEN        Plex authentication token
  PLEX_DRY_RUN      Set to 'false' to execute (default: true)
  PLEX_NO_CONFIRM   Set to 'true' to skip confirmation prompts
  PLEX_DEBUG        Set to 'true' to enable debug logging

Docker Example:
  docker run -e PLEX_URL=http://host.docker.internal:32400 -e PLEX_TOKEN=xyz123 plex-clean

Both command line arguments and environment variables are supported.
Command line arguments take precedence over environment variables.
        """
    )

    # Command line arguments (optional if env vars are provided)
    parser.add_argument(
        "--server-url",
        help="Plex server URL (can also use PLEX_URL env var)"
    )
    parser.add_argument(
        "--token",
        help="Plex authentication token (can also use PLEX_TOKEN env var)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually remove collections (overrides --dry-run and PLEX_DRY_RUN)"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Don't ask for confirmation before removing collections"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Get configuration from args or environment variables
    server_url = args.server_url or get_env_var('PLEX_URL', required=True)
    token = args.token or get_env_var('PLEX_TOKEN', required=True)

    # Debug mode from args or env
    debug_mode = args.debug or get_env_var('PLEX_DEBUG', 'false').lower() == 'true'
    setup_logging(debug_mode)

    # Log startup information
    logging.info("🐳 PLEX COLLECTION CLEANUP - DOCKER READY")
    logging.info("=" * 50)
    logging.info("Configuration:")
    logging.info(f"  Server URL: {server_url}")
    logging.info(f"  Token: {'*' * (len(token) - 4)}{token[-4:]}")
    logging.info(f"  Debug mode: {debug_mode}")

    # Execution mode logic
    if args.execute:
        dry_run = False
        logging.info("  Mode: EXECUTE (from --execute flag)")
    else:
        env_dry_run = get_env_var('PLEX_DRY_RUN', 'true').lower()
        dry_run = env_dry_run != 'false'
        source = "environment variable" if not args.dry_run else "default"
        logging.info(f"  Mode: {'DRY RUN' if dry_run else 'EXECUTE'} (from {source})")

    # Confirmation settings
    if args.no_confirm:
        confirm = False
        logging.info("  Confirmation: DISABLED (from --no-confirm flag)")
    else:
        env_no_confirm = get_env_var('PLEX_NO_CONFIRM', 'false').lower()
        confirm = env_no_confirm != 'true'
        source = "environment variable" if env_no_confirm == 'true' else "default"
        logging.info(f"  Confirmation: {'ENABLED' if confirm else 'DISABLED'} (from {source})")

    # Label deletion configuration
    delete_labels = parse_label_list(get_env_var('PLEX_DELETE_LABELS', ''))
    delete_patterns = parse_label_list(get_env_var('PLEX_DELETE_LABEL_PATTERNS', ''))

    logging.info(f"  Delete labels: {delete_labels if delete_labels else 'None'}")
    logging.info(f"  Delete patterns: {delete_patterns if delete_patterns else 'None'}")
    logging.info("=" * 50)

    if dry_run:
        logging.info("🔍 Running in DRY RUN mode - no collections will be removed")
        logging.info("💡 Set PLEX_DRY_RUN=false or use --execute to actually remove collections")
    else:
        logging.warning("⚠️  EXECUTE mode - collections WILL BE PERMANENTLY REMOVED!")

    logging.info("\n📋 Deletion Rules:")
    logging.info("  ✓ Always remove collections WITHOUT any labels")
    if delete_labels:
        logging.info(f"  ✓ Remove collections WITH exact labels: {delete_labels}")
    if delete_patterns:
        logging.info(f"  ✓ Remove collections WITH labels matching patterns: {delete_patterns}")
    if not delete_labels and not delete_patterns:
        logging.info("  • No additional label-based removal rules configured")

    # Connect and run cleanup
    plex = connect_to_plex(server_url, token)
    cleanup_collections(plex, dry_run=dry_run, confirm=confirm, delete_labels=delete_labels, delete_patterns=delete_patterns)


if __name__ == "__main__":
    main()