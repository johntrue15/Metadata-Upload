#!/usr/bin/env python3
"""
File Watcher GitHub Committer

A script that watches a folder for new files and automatically commits them to a GitHub repository.

Usage:
    python file_watcher_github.py <folder_path> <repo_url>
    python file_watcher_github.py <folder_path> <repo_url> --token <github_token>

Example:
    python file_watcher_github.py /path/to/watch https://github.com/username/repo.git
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import git
from git import Repo, InvalidGitRepositoryError

# =============================================================================
# CONFIGURATION SECTION - SECURE TOKEN HANDLING
# =============================================================================

# Option 1: Environment variable (recommended for PyCharm and development)
ENV_VAR_NAME = "REPO_TOKEN"

# Option 2: Config file path (secure local storage)
CONFIG_FILE = ".github_config"

# NOTE: Do not embed tokens directly in this file as it's a public repository!
# Use environment variables or config files instead.

# =============================================================================


class GitHubFileHandler(FileSystemEventHandler):
    """Handle file system events and commit new files to GitHub."""
    
    def __init__(self, watch_folder, github_token, repo_url):
        self.watch_folder = Path(watch_folder).resolve()
        self.github_token = github_token
        self.repo_url = repo_url
        self.repo_path = self.watch_folder / '.git'
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize or connect to git repository
        self.setup_repository()
    
    def setup_repository(self):
        """Initialize git repository or connect to existing one."""
        try:
            # Try to open existing repository
            self.repo = Repo(self.watch_folder)
            self.logger.info(f"Connected to existing git repository at {self.watch_folder}")
        except InvalidGitRepositoryError:
            # Initialize new repository
            self.logger.info(f"Initializing new git repository at {self.watch_folder}")
            self.repo = Repo.init(self.watch_folder)
            
            # Add remote origin with token authentication
            remote_url = self.get_authenticated_url()
            try:
                origin = self.repo.create_remote('origin', remote_url)
                self.logger.info(f"Added remote origin: {self.repo_url}")
            except git.exc.GitCommandError as e:
                self.logger.error(f"Failed to add remote: {e}")
                
        # Configure git user (required for commits)
        try:
            self.repo.config_writer().set_value("user", "name", "File Watcher Bot").release()
            self.repo.config_writer().set_value("user", "email", "filewatcher@automated.com").release()
        except Exception as e:
            self.logger.warning(f"Could not set git config: {e}")
    
    def get_authenticated_url(self):
        """Create GitHub URL with token authentication."""
        if self.repo_url.startswith('https://github.com/'):
            # Replace https://github.com/ with https://token@github.com/
            return self.repo_url.replace('https://github.com/', f'https://{self.github_token}@github.com/')
        elif self.repo_url.startswith('git@github.com:'):
            # Convert SSH to HTTPS with token
            repo_part = self.repo_url.replace('git@github.com:', '').replace('.git', '')
            return f'https://{self.github_token}@github.com/{repo_part}.git'
        else:
            # Assume it's already a properly formatted URL
            return self.repo_url
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            # Skip git files and hidden files
            if not any(part.startswith('.') for part in file_path.parts):
                self.logger.info(f"New file detected: {file_path}")
                self.commit_file(file_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            # Skip git files and hidden files
            if not any(part.startswith('.') for part in file_path.parts):
                self.logger.info(f"File modified: {file_path}")
                self.commit_file(file_path)
    
    def commit_file(self, file_path):
        """Commit a single file to the repository."""
        try:
            # Get relative path from repository root
            rel_path = file_path.relative_to(self.watch_folder)
            
            # Add file to staging area
            self.repo.index.add([str(rel_path)])
            
            # Create commit
            commit_message = f"Auto-commit: {rel_path.name}"
            commit = self.repo.index.commit(commit_message)
            self.logger.info(f"Committed file: {rel_path} (commit: {commit.hexsha[:8]})")
            
            # Push to remote
            self.push_to_remote()
            
        except Exception as e:
            self.logger.error(f"Failed to commit file {file_path}: {e}")
    
    def push_to_remote(self):
        """Push commits to remote repository."""
        try:
            # Get or create origin remote
            if 'origin' not in [remote.name for remote in self.repo.remotes]:
                remote_url = self.get_authenticated_url()
                origin = self.repo.create_remote('origin', remote_url)
            else:
                origin = self.repo.remotes.origin
                # Update URL with token
                origin.set_url(self.get_authenticated_url())
            
            # Push to main/master branch
            current_branch = self.repo.active_branch.name
            origin.push(current_branch)
            self.logger.info(f"Successfully pushed to remote repository")
            
        except Exception as e:
            self.logger.error(f"Failed to push to remote: {e}")


def get_github_token(provided_token=None):
    """Get GitHub token from various sources in order of preference."""
    
    # 1. Command line argument (highest priority)
    if provided_token:
        return provided_token
    
    # 2. Environment variable
    env_token = os.getenv(ENV_VAR_NAME)
    if env_token:
        print(f"✅ Using GitHub token from environment variable: {ENV_VAR_NAME}")
        return env_token
    
    # 3. Config file
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        try:
            token = config_path.read_text().strip()
            if token:
                print(f"✅ Using GitHub token from config file: {CONFIG_FILE}")
                return token
        except Exception as e:
            print(f"⚠️  Could not read config file {CONFIG_FILE}: {e}")
    
    # No token found
    return None


def create_config_file(token):
    """Create a config file with the GitHub token."""
    config_path = Path(CONFIG_FILE)
    try:
        config_path.write_text(token)
        config_path.chmod(0o600)  # Restrict file permissions
        print(f"✅ GitHub token saved to config file: {CONFIG_FILE}")
        print("⚠️  Remember to add this file to your .gitignore!")
    except Exception as e:
        print(f"❌ Failed to create config file: {e}")


def validate_inputs(folder_path, repo_url):
    """Validate input parameters."""
    # Check if folder exists
    if not Path(folder_path).exists():
        raise ValueError(f"Folder does not exist: {folder_path}")
    
    if not Path(folder_path).is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")
    
    # Basic validation for repository URL
    if not any(pattern in repo_url for pattern in ['github.com', 'github']):
        raise ValueError("Repository URL should be a GitHub repository")
    
    return True


def main():
    """Main function to set up file watching."""
    parser = argparse.ArgumentParser(
        description="Watch a folder for new files and commit them to GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use embedded token or environment variable
  python file_watcher_github.py /path/to/watch https://github.com/user/repo.git
  
  # Provide token explicitly
  python file_watcher_github.py /path/to/watch https://github.com/user/repo.git --token ghp_1234567890abcdef
  
  # Save token to config file
  python file_watcher_github.py --save-token ghp_1234567890abcdef
  
Environment Variable:
  export REPO_TOKEN="your_token_here"
  python file_watcher_github.py /path/to/watch https://github.com/user/repo.git
        """
    )
    
    parser.add_argument('folder_path', nargs='?', help='Path to the folder to watch')
    parser.add_argument('repo_url', nargs='?', help='GitHub repository URL (HTTPS or SSH)')
    parser.add_argument('--token', '-t', help='GitHub personal access token (optional if embedded or in env)')
    parser.add_argument('--save-token', help='Save GitHub token to config file and exit')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Handle token saving
    if args.save_token:
        create_config_file(args.save_token)
        return
    
    # Validate required arguments
    if not args.folder_path or not args.repo_url:
        parser.error("folder_path and repo_url are required unless using --save-token")
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Get GitHub token from various sources
        github_token = get_github_token(args.token)
        if not github_token:
            print("❌ No GitHub token found!")
            print("\nPlease provide a token using one of these methods:")
            print("1. Set environment variable: export REPO_TOKEN='your_token'")
            print("2. Create config file: python file_watcher_github.py --save-token your_token")
            print("3. Provide as argument: python file_watcher_github.py folder repo --token your_token")
            sys.exit(1)
        
        # Validate token
        if len(github_token) < 10:
            raise ValueError("Invalid GitHub token provided")
        
        # Validate other inputs
        validate_inputs(args.folder_path, args.repo_url)
        
        # Setup file watcher
        event_handler = GitHubFileHandler(args.folder_path, github_token, args.repo_url)
        observer = Observer()
        observer.schedule(event_handler, args.folder_path, recursive=True)
        
        # Start watching
        observer.start()
        print(f"🔍 Watching folder: {args.folder_path}")
        print(f"📁 Repository: {args.repo_url}")
        print("📝 File watcher is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n👋 File watcher stopped.")
            
        observer.join()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
