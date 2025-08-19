#!/usr/bin/env python3
"""
Network File Watcher GitHub Committer

A script that watches a network drive for new files, copies them to a local Git repository,
and automatically commits them to a GitHub repository.

Usage:
    python network_file_watcher_github.py <network_path> <local_git_path> <repo_url>
    python network_file_watcher_github.py <network_path> <local_git_path> <repo_url> --token <github_token>

Example:
    python network_file_watcher_github.py "\\server\share" "C:\GitRepo" https://github.com/username/repo.git
"""

import os
import sys
import time
import logging
import argparse
import shutil
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


class NetworkFileHandler(FileSystemEventHandler):
    """Handle file system events from network drive and sync to local Git repository."""
    
    def __init__(self, network_path, local_git_path, github_token, repo_url):
        self.network_path = Path(network_path).resolve()
        self.local_git_path = Path(local_git_path).resolve()
        self.github_token = github_token
        self.repo_url = repo_url
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure local Git path exists
        self.local_git_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize or connect to git repository
        self.setup_repository()
        
        # Track processed files to avoid duplicates
        self.processed_files = set()
    
    def setup_repository(self):
        """Initialize git repository or connect to existing one."""
        try:
            # Try to open existing repository
            self.repo = Repo(self.local_git_path)
            self.logger.info(f"Connected to existing git repository at {self.local_git_path}")
        except InvalidGitRepositoryError:
            # Initialize new repository
            self.logger.info(f"Initializing new git repository at {self.local_git_path}")
            self.repo = Repo.init(self.local_git_path)
            
            # Add remote origin with token authentication
            remote_url = self.get_authenticated_url()
            try:
                origin = self.repo.create_remote('origin', remote_url)
                self.logger.info(f"Added remote origin: {self.repo_url}")
            except git.exc.GitCommandError as e:
                self.logger.error(f"Failed to add remote: {e}")
                
        # Configure git user (required for commits)
        try:
            self.repo.config_writer().set_value("user", "name", "Network File Watcher Bot").release()
            self.repo.config_writer().set_value("user", "email", "networkwatcher@automated.com").release()
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
    
    def get_relative_path(self, file_path):
        """Get relative path from network root."""
        try:
            return file_path.relative_to(self.network_path)
        except ValueError:
            # If file is not under network path, use just the filename
            return Path(file_path.name)
    
    def copy_file_to_local(self, source_path):
        """Copy file from network drive to local git repository."""
        try:
            # Get relative path to preserve directory structure
            rel_path = self.get_relative_path(source_path)
            dest_path = self.local_git_path / rel_path
            
            # Create destination directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            self.logger.info(f"Copied {source_path} → {dest_path}")
            
            return dest_path
            
        except Exception as e:
            self.logger.error(f"Failed to copy file {source_path}: {e}")
            return None
    
    def on_created(self, event):
        """Handle file creation events from network drive."""
        if not event.is_directory:
            self.handle_file_event(event.src_path, "created")
    
    def on_modified(self, event):
        """Handle file modification events from network drive."""
        if not event.is_directory:
            self.handle_file_event(event.src_path, "modified")
    
    def handle_file_event(self, file_path_str, event_type):
        """Handle file events (created or modified)."""
        file_path = Path(file_path_str)
        
        # Skip git files, hidden files, and temporary files
        if self.should_skip_file(file_path):
            return
        
        # Avoid processing the same file multiple times quickly
        file_key = f"{file_path}:{file_path.stat().st_mtime}"
        if file_key in self.processed_files:
            return
        
        self.processed_files.add(file_key)
        
        # Clean up old entries to prevent memory buildup
        if len(self.processed_files) > 1000:
            self.processed_files.clear()
        
        self.logger.info(f"Network file {event_type}: {file_path}")
        
        # Wait a moment for file to be completely written
        time.sleep(0.5)
        
        # Copy to local git repository
        dest_path = self.copy_file_to_local(file_path)
        if dest_path:
            self.commit_and_push_file(dest_path)
    
    def should_skip_file(self, file_path):
        """Check if file should be skipped."""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return True
        
        # Skip temporary files
        temp_extensions = {'.tmp', '.temp', '~'}
        if file_path.suffix.lower() in temp_extensions:
            return True
        
        # Skip files that start with ~$ (Office temp files)
        if file_path.name.startswith('~$'):
            return True
        
        return False
    
    def commit_and_push_file(self, local_file_path):
        """Commit a file from the local repository and push to GitHub."""
        try:
            # Get relative path from repository root
            rel_path = local_file_path.relative_to(self.local_git_path)
            
            # Add file to staging area
            self.repo.index.add([str(rel_path)])
            
            # Check if there are any changes to commit
            if self.repo.index.diff("HEAD"):
                # Create commit
                commit_message = f"Auto-commit from network: {rel_path.name}"
                commit = self.repo.index.commit(commit_message)
                self.logger.info(f"Committed file: {rel_path} (commit: {commit.hexsha[:8]})")
                
                # Push to remote
                self.push_to_remote()
            else:
                self.logger.info(f"No changes to commit for {rel_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to commit file {local_file_path}: {e}")
    
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


def validate_inputs(network_path, local_git_path, repo_url):
    """Validate input parameters."""
    # Check if network path exists
    if not Path(network_path).exists():
        raise ValueError(f"Network path does not exist: {network_path}")
    
    if not Path(network_path).is_dir():
        raise ValueError(f"Network path is not a directory: {network_path}")
    
    # Check if local path can be created
    local_path = Path(local_git_path)
    try:
        local_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Cannot create local git path {local_git_path}: {e}")
    
    # Basic validation for repository URL
    if not any(pattern in repo_url for pattern in ['github.com', 'github']):
        raise ValueError("Repository URL should be a GitHub repository")
    
    return True


def main():
    """Main function to set up network file watching."""
    parser = argparse.ArgumentParser(
        description="Watch a network drive for new files and commit them to GitHub via local repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use embedded token or environment variable
  python network_file_watcher_github.py "\\\\server\\share" "C:\\GitRepo" https://github.com/user/repo.git
  
  # Provide token explicitly
  python network_file_watcher_github.py "Z:\\NetworkFolder" "C:\\GitRepo" https://github.com/user/repo.git --token ghp_1234567890abcdef
  
  # Save token to config file
  python network_file_watcher_github.py --save-token ghp_1234567890abcdef
  
Environment Variable:
  set REPO_TOKEN=your_token_here
  python network_file_watcher_github.py "\\\\server\\share" "C:\\GitRepo" https://github.com/user/repo.git
        """
    )
    
    parser.add_argument('network_path', nargs='?', help='Path to the network drive/folder to watch')
    parser.add_argument('local_git_path', nargs='?', help='Local path for Git repository')
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
    if not args.network_path or not args.local_git_path or not args.repo_url:
        parser.error("network_path, local_git_path, and repo_url are required unless using --save-token")
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Get GitHub token from various sources
        github_token = get_github_token(args.token)
        if not github_token:
            print("❌ No GitHub token found!")
            print("\nPlease provide a token using one of these methods:")
            print("1. Set environment variable: set REPO_TOKEN=your_token")
            print("2. Create config file: python network_file_watcher_github.py --save-token your_token")
            print("3. Provide as argument: python network_file_watcher_github.py network local repo --token your_token")
            sys.exit(1)
        
        # Validate token
        if len(github_token) < 10:
            raise ValueError("Invalid GitHub token provided")
        
        # Validate other inputs
        validate_inputs(args.network_path, args.local_git_path, args.repo_url)
        
        # Setup file watcher
        event_handler = NetworkFileHandler(args.network_path, args.local_git_path, github_token, args.repo_url)
        observer = Observer()
        observer.schedule(event_handler, args.network_path, recursive=True)
        
        # Start watching
        observer.start()
        print(f"🔍 Watching network path: {args.network_path}")
        print(f"📁 Local Git repository: {args.local_git_path}")
        print(f"📤 GitHub repository: {args.repo_url}")
        print("📝 Network file watcher is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n👋 Network file watcher stopped.")
            
        observer.join()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
