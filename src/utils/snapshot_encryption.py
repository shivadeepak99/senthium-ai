"""
Snapshot Encryption - Encrypt/decrypt security snapshots for privacy

Protects sensitive facial images with AES encryption! 🔒🛡️
"""

import logging
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

logger = logging.getLogger(__name__)


class SnapshotEncryption:
    """
    Encrypt and decrypt snapshot files using Fernet (AES-128).
    
    Keeps your facial data private and secure! 🔐💖
    """
    
    def __init__(self, key_file: str = "config/.snapshot_key"):
        """
        Initialize encryption manager.
        
        Args:
            key_file: Path to store encryption key (will be created if missing)
        """
        self.key_file = Path(key_file)
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or generate encryption key
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        
        logger.info("🔒 Snapshot encryption initialized")
    
    def _load_or_generate_key(self) -> bytes:
        """
        Load existing key or generate a new one.
        
        Returns:
            Encryption key (bytes)
        """
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                logger.debug("🔑 Loaded existing encryption key")
                return key
            except Exception as e:
                logger.warning(f"⚠️ Failed to load key, generating new one: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        try:
            # Save key to file with restricted permissions
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Set file permissions (Windows: remove inheritance, *nix: 600)
            try:
                if os.name == 'nt':  # Windows
                    import subprocess
                    # Remove inherited permissions and grant only current user access
                    subprocess.run(
                        ['icacls', str(self.key_file), '/inheritance:r', '/grant:r', f'{os.getlogin()}:F'],
                        capture_output=True,
                        check=False
                    )
                else:  # Unix/Linux/Mac
                    os.chmod(self.key_file, 0o600)
            except Exception as e:
                logger.warning(f"⚠️ Could not set restrictive permissions on key file: {e}")
            
            logger.info(f"🔑 Generated new encryption key: {self.key_file}")
            return key
            
        except Exception as e:
            logger.error(f"❌ Failed to save encryption key: {e}")
            # Return key anyway (will work in memory, just not persisted)
            return key
    
    def encrypt_file(self, input_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Encrypt a snapshot file.
        
        Args:
            input_path: Path to original snapshot
            output_path: Path to save encrypted file (default: adds .encrypted suffix)
        
        Returns:
            Path to encrypted file, or None if failed
        """
        try:
            input_file = Path(input_path)
            
            if not input_file.exists():
                logger.error(f"❌ Input file not found: {input_path}")
                return None
            
            # Read original file
            with open(input_file, 'rb') as f:
                plaintext = f.read()
            
            # Encrypt
            ciphertext = self.cipher.encrypt(plaintext)
            
            # Determine output path
            if output_path is None:
                output_file = input_file.parent / f"{input_file.name}.encrypted"
            else:
                output_file = Path(output_path)
            
            # Write encrypted file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'wb') as f:
                f.write(ciphertext)
            
            logger.debug(f"🔒 Encrypted: {input_file.name} → {output_file.name}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            return None
    
    def decrypt_file(self, input_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Decrypt a snapshot file.
        
        Args:
            input_path: Path to encrypted snapshot
            output_path: Path to save decrypted file (default: removes .encrypted suffix)
        
        Returns:
            Path to decrypted file, or None if failed
        """
        try:
            input_file = Path(input_path)
            
            if not input_file.exists():
                logger.error(f"❌ Input file not found: {input_path}")
                return None
            
            # Read encrypted file
            with open(input_file, 'rb') as f:
                ciphertext = f.read()
            
            # Decrypt
            plaintext = self.cipher.decrypt(ciphertext)
            
            # Determine output path
            if output_path is None:
                if input_file.name.endswith('.encrypted'):
                    output_file = input_file.parent / input_file.name.replace('.encrypted', '')
                else:
                    output_file = input_file.parent / f"{input_file.stem}_decrypted{input_file.suffix}"
            else:
                output_file = Path(output_path)
            
            # Write decrypted file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'wb') as f:
                f.write(plaintext)
            
            logger.debug(f"🔓 Decrypted: {input_file.name} → {output_file.name}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            return None
    
    def encrypt_directory(self, directory: str, pattern: str = "*.jpg", delete_originals: bool = False) -> int:
        """
        Encrypt all matching files in a directory.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern for files to encrypt
            delete_originals: Delete original files after encryption (DANGEROUS!)
        
        Returns:
            Number of files encrypted
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                logger.error(f"❌ Directory not found: {directory}")
                return 0
            
            files = list(dir_path.glob(pattern))
            encrypted_count = 0
            
            for file_path in files:
                # Skip already encrypted files
                if file_path.name.endswith('.encrypted'):
                    continue
                
                encrypted_path = self.encrypt_file(str(file_path))
                
                if encrypted_path:
                    encrypted_count += 1
                    
                    if delete_originals:
                        try:
                            file_path.unlink()
                            logger.debug(f"🗑️ Deleted original: {file_path.name}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to delete original: {e}")
            
            logger.info(f"🔒 Encrypted {encrypted_count}/{len(files)} files in {directory}")
            return encrypted_count
            
        except Exception as e:
            logger.error(f"❌ Directory encryption failed: {e}")
            return 0
    
    def decrypt_directory(self, directory: str, pattern: str = "*.encrypted", delete_encrypted: bool = False) -> int:
        """
        Decrypt all matching files in a directory.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern for files to decrypt
            delete_encrypted: Delete encrypted files after decryption
        
        Returns:
            Number of files decrypted
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                logger.error(f"❌ Directory not found: {directory}")
                return 0
            
            files = list(dir_path.glob(pattern))
            decrypted_count = 0
            
            for file_path in files:
                decrypted_path = self.decrypt_file(str(file_path))
                
                if decrypted_path:
                    decrypted_count += 1
                    
                    if delete_encrypted:
                        try:
                            file_path.unlink()
                            logger.debug(f"🗑️ Deleted encrypted file: {file_path.name}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to delete encrypted file: {e}")
            
            logger.info(f"🔓 Decrypted {decrypted_count}/{len(files)} files in {directory}")
            return decrypted_count
            
        except Exception as e:
            logger.error(f"❌ Directory decryption failed: {e}")
            return 0
    
    def is_encrypted(self, file_path: str) -> bool:
        """
        Check if a file is encrypted (by trying to decrypt it).
        
        Args:
            file_path: Path to check
        
        Returns:
            True if file appears to be encrypted
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read(100)  # Read first 100 bytes
            
            # Try to decrypt (Fernet will raise InvalidToken if not encrypted)
            self.cipher.decrypt(data[:100] if len(data) >= 100 else data)
            return True
            
        except Exception:
            return False
    
    def get_stats(self) -> dict:
        """Get encryption statistics."""
        return {
            "key_file": str(self.key_file),
            "key_exists": self.key_file.exists(),
            "encryption_algorithm": "Fernet (AES-128 CBC + HMAC)"
        }


# Convenience functions for quick use
def encrypt_snapshot(input_path: str, output_path: Optional[str] = None, key_file: str = "config/.snapshot_key") -> Optional[str]:
    """Quick encrypt a single snapshot."""
    encryptor = SnapshotEncryption(key_file)
    return encryptor.encrypt_file(input_path, output_path)


def decrypt_snapshot(input_path: str, output_path: Optional[str] = None, key_file: str = "config/.snapshot_key") -> Optional[str]:
    """Quick decrypt a single snapshot."""
    encryptor = SnapshotEncryption(key_file)
    return encryptor.decrypt_file(input_path, output_path)
