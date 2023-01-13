from unittest.mock import patch


def mock_upgrade_paths(new: dict):
    python_path = "openforms.upgrades.upgrade_paths.UPGRADE_PATHS"
    return patch(python_path, new=new)
