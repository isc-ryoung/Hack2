"""Unit tests for CPF manager read/write operations."""

import pytest
import tempfile
from pathlib import Path
from src.services.cpf_manager import CPFManager


@pytest.fixture
def temp_cpf_file():
    """Create a temporary CPF file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cpf') as f:
        f.write("[Startup]\n")
        f.write("globals=10000\n")
        f.write("routines=5000\n")
        f.write("\n")
        f.write("[config]\n")
        f.write("bbsiz=32768\n")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()
    backup_dir = temp_path.parent / "backups"
    if backup_dir.exists():
        for backup in backup_dir.glob("*.cpf.backup.*"):
            backup.unlink()
        backup_dir.rmdir()


def test_cpf_manager_initialization(temp_cpf_file):
    """Test CPF manager initialization."""
    manager = CPFManager(temp_cpf_file)
    assert manager.cpf_path == temp_cpf_file
    assert manager.backup_dir.exists()


def test_read_setting(temp_cpf_file):
    """Test reading a configuration setting."""
    manager = CPFManager(temp_cpf_file)
    
    value = manager.read_setting("Startup", "globals")
    assert value == "10000"
    
    value = manager.read_setting("Startup", "routines")
    assert value == "5000"


def test_read_setting_not_found(temp_cpf_file):
    """Test reading non-existent setting."""
    manager = CPFManager(temp_cpf_file)
    
    value = manager.read_setting("Startup", "nonexistent")
    assert value is None


def test_write_setting(temp_cpf_file):
    """Test writing a configuration setting."""
    manager = CPFManager(temp_cpf_file)
    
    success, backup_path = manager.write_setting("Startup", "globals", "20000")
    
    assert success
    assert backup_path is not None
    assert Path(backup_path).exists()
    
    # Verify value changed
    new_value = manager.read_setting("Startup", "globals")
    assert new_value == "20000"


def test_write_setting_new_key(temp_cpf_file):
    """Test writing a new configuration key."""
    manager = CPFManager(temp_cpf_file)
    
    success, _ = manager.write_setting("Startup", "newkey", "12345")
    
    assert success
    value = manager.read_setting("Startup", "newkey")
    assert value == "12345"


def test_write_setting_new_section(temp_cpf_file):
    """Test writing to a new section."""
    manager = CPFManager(temp_cpf_file)
    
    success, _ = manager.write_setting("NewSection", "newkey", "value")
    
    assert success
    value = manager.read_setting("NewSection", "newkey")
    assert value == "value"


def test_create_backup(temp_cpf_file):
    """Test backup creation."""
    manager = CPFManager(temp_cpf_file)
    
    backup_path = manager.create_backup()
    
    assert backup_path is not None
    assert Path(backup_path).exists()
    assert "iris.cpf.backup." in backup_path


def test_restore_backup(temp_cpf_file):
    """Test backup restoration."""
    manager = CPFManager(temp_cpf_file)
    
    # Create backup
    backup_path = manager.create_backup()
    
    # Modify original
    manager.write_setting("Startup", "globals", "99999", create_backup=False)
    assert manager.read_setting("Startup", "globals") == "99999"
    
    # Restore backup
    success = manager.restore_backup(backup_path)
    assert success
    
    # Verify restored value
    value = manager.read_setting("Startup", "globals")
    assert value == "10000"


def test_validate_cpf(temp_cpf_file):
    """Test CPF validation."""
    manager = CPFManager(temp_cpf_file)
    
    is_valid = manager.validate_cpf()
    assert is_valid


def test_requires_restart():
    """Test restart requirement determination."""
    manager = CPFManager(Path("/fake/path/iris.cpf"))
    
    # Startup section always requires restart
    assert manager.requires_restart("Startup", "globals") == True
    assert manager.requires_restart("Startup", "routines") == True
    
    # Config section requires restart
    assert manager.requires_restart("config", "anykey") == True
    
    # Key-based restart requirements
    assert manager.requires_restart("OtherSection", "globals") == True
    assert manager.requires_restart("OtherSection", "wijdir") == True
    
    # Non-restart setting
    assert manager.requires_restart("OtherSection", "somekey") == False


def test_get_all_sections(temp_cpf_file):
    """Test getting all CPF sections."""
    manager = CPFManager(temp_cpf_file)
    
    sections = manager.get_all_sections()
    
    assert "Startup" in sections
    assert "config" in sections
    assert sections["Startup"]["globals"] == "10000"
    assert sections["Startup"]["routines"] == "5000"
