"""
Settings Migration Tool

This tool helps migrate existing settings from the old centralized storage
to the new application-specific storage structure, ensuring backward compatibility
during the transition to the standardized settings system.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.system.utils.PathResolver import PathResolver, PathType
from backend.system.utils.ApplicationStorageResolver import get_application_storage_resolver


class SettingsMigrationTool:
    """
    Tool for migrating settings from old structure to new application-specific structure.
    """
    
    def __init__(self):
        """Initialize the migration tool."""
        self.path_resolver = PathResolver()
        self.app_storage_resolver = get_application_storage_resolver()
        self.old_settings_path = self.path_resolver.get_path(PathType.SETTINGS_STORAGE)
        
        # Define migration mappings
        # CORE SETTINGS: camera_settings.json and robot_config.json 
        # - Required by ALL applications (base controllers/services need them)
        # - Each app gets its own copy
        
        # APPLICATION-SPECIFIC SETTINGS: glue_settings.json, glue_cell_config.json, etc.
        # - Only specific to certain applications
        # - Registered by application when loaded
        
        self.migration_mappings = {
            # Application-specific settings (only for glue app)
            "glue_settings.json": {
                "app_name": "glue_dispensing_application",
                "settings_type": "glue_settings"
            },
            "glue_cell_config.json": {
                "app_name": "glue_dispensing_application", 
                "settings_type": "glue_cell_config"
            },
        }
        
        # Core settings that EVERY application needs
        # These will be copied to each application's storage
        self.core_settings = {
            "camera_settings.json": "camera_settings",
            "robot_config.json": "robot_config"
        }
    
    def check_migration_needed(self) -> Tuple[bool, List[str]]:
        """
        Check if migration is needed and which files require migration.
        
        Returns:
            Tuple[bool, List[str]]: (migration_needed, list_of_files_to_migrate)
        """
        files_to_migrate = []
        
        if not self.old_settings_path.exists():
            return False, files_to_migrate
        
        for filename, mapping in self.migration_mappings.items():
            old_file_path = self.old_settings_path / filename
            if old_file_path.exists():
                # Check if it's already migrated
                new_file_path = self.app_storage_resolver.get_settings_path(
                    mapping["app_name"], 
                    mapping["settings_type"]
                )
                
                if not os.path.exists(new_file_path):
                    files_to_migrate.append(filename)
        
        return len(files_to_migrate) > 0, files_to_migrate
    
    def migrate_file(self, filename: str, backup: bool = True) -> Tuple[bool, str]:
        """
        Migrate a single settings file to the new structure.
        
        Args:
            filename: Name of the file to migrate
            backup: Whether to create a backup of the original file
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if filename not in self.migration_mappings:
            return False, f"No migration mapping defined for {filename}"
        
        mapping = self.migration_mappings[filename]
        old_file_path = self.old_settings_path / filename
        
        if not old_file_path.exists():
            return False, f"Source file {old_file_path} does not exist"
        
        try:
            # Get new file path
            new_file_path = self.app_storage_resolver.get_settings_path(
                mapping["app_name"], 
                mapping["settings_type"],
                create_if_missing=True
            )
            
            # Create backup if requested
            if backup:
                backup_path = f"{old_file_path}.backup"
                shutil.copy2(old_file_path, backup_path)
                print(f"Created backup: {backup_path}")
            
            # Copy file to new location
            shutil.copy2(old_file_path, new_file_path)
            
            print(f"Migrated {filename}: {old_file_path} -> {new_file_path}")
            return True, f"Successfully migrated {filename}"
            
        except Exception as e:
            return False, f"Error migrating {filename}: {str(e)}"
    
    def migrate_all_files(self, backup: bool = True) -> Dict[str, Tuple[bool, str]]:
        """
        Migrate all files that need migration.
        
        Args:
            backup: Whether to create backups of original files
            
        Returns:
            Dict[str, Tuple[bool, str]]: Results for each file (filename -> (success, message))
        """
        migration_needed, files_to_migrate = self.check_migration_needed()
        results = {}
        
        if not migration_needed:
            print("No migration needed - all files are already in the correct location")
            return results
        
        print(f"Migrating {len(files_to_migrate)} files...")
        
        for filename in files_to_migrate:
            success, message = self.migrate_file(filename, backup)
            results[filename] = (success, message)
            
            if success:
                print(f"✅ {filename}: {message}")
            else:
                print(f"❌ {filename}: {message}")
        
        return results
    
    def verify_migration(self) -> Tuple[bool, Dict[str, bool]]:
        """
        Verify that migration was successful by checking if files exist in new locations.
        
        Returns:
            Tuple[bool, Dict[str, bool]]: (all_successful, per_file_status)
        """
        verification_results = {}
        
        for filename, mapping in self.migration_mappings.items():
            new_file_path = self.app_storage_resolver.get_settings_path(
                mapping["app_name"], 
                mapping["settings_type"]
            )
            
            exists = os.path.exists(new_file_path)
            verification_results[filename] = exists
            
            if exists:
                print(f"✅ {filename} found at new location: {new_file_path}")
            else:
                print(f"❌ {filename} NOT found at new location: {new_file_path}")
        
        all_successful = all(verification_results.values())
        return all_successful, verification_results
    
    def create_application_structures(self) -> Dict[str, bool]:
        """
        Create directory structures for all known applications.
        
        Returns:
            Dict[str, bool]: Results for each application (app_name -> success)
        """
        results = {}
        
        # Extract unique app names from migration mappings
        app_names = set(mapping["app_name"] for mapping in self.migration_mappings.values())
        
        for app_name in app_names:
            success = self.app_storage_resolver.create_application_structure(app_name)
            results[app_name] = success
            
            if success:
                print(f"✅ Created structure for {app_name}")
            else:
                print(f"❌ Failed to create structure for {app_name}")
        
        return results
    
    def cleanup_old_files(self, confirm: bool = False) -> Dict[str, Tuple[bool, str]]:
        """
        Clean up old settings files after successful migration.
        
        Args:
            confirm: If True, actually delete the files. If False, just report what would be deleted.
            
        Returns:
            Dict[str, Tuple[bool, str]]: Results for each file cleanup
        """
        results = {}
        
        # First verify migration was successful
        migration_successful, verification_results = self.verify_migration()
        
        if not migration_successful:
            print("❌ Migration verification failed. Skipping cleanup.")
            return results
        
        for filename in self.migration_mappings.keys():
            old_file_path = self.old_settings_path / filename
            backup_path = f"{old_file_path}.backup"
            
            if old_file_path.exists():
                if confirm:
                    try:
                        os.remove(old_file_path)
                        results[filename] = (True, f"Deleted {old_file_path}")
                        print(f"🗑️ Deleted: {old_file_path}")
                    except Exception as e:
                        results[filename] = (False, f"Failed to delete {old_file_path}: {e}")
                        print(f"❌ Failed to delete: {old_file_path}")
                else:
                    results[filename] = (True, f"Would delete: {old_file_path}")
                    print(f"📋 Would delete: {old_file_path}")
            
            # Also report on backup files
            if os.path.exists(backup_path):
                backup_key = f"{filename}.backup"
                if confirm:
                    print(f"💾 Backup preserved: {backup_path}")
                else:
                    print(f"💾 Backup would be preserved: {backup_path}")
        
        if not confirm:
            print("\n⚠️ This was a dry run. Use confirm=True to actually delete files.")
        
        return results
    
    def get_migration_report(self) -> Dict[str, any]:
        """
        Generate a comprehensive migration report.
        
        Returns:
            Dict[str, any]: Complete migration status report
        """
        migration_needed, files_to_migrate = self.check_migration_needed()
        verification_successful, verification_results = self.verify_migration()
        
        # Check which core settings exist
        existing_system_settings = {}
        for filename, description in self.core_settings.items():
            file_path = self.old_settings_path / filename
            existing_system_settings[filename] = {
                "exists": file_path.exists(),
                "description": description,
                "path": str(file_path)
            }
        
        report = {
            "migration_needed": migration_needed,
            "files_to_migrate": files_to_migrate,
            "verification_successful": verification_successful,
            "verification_results": verification_results,
            "old_settings_path": str(self.old_settings_path),
            "migration_mappings": self.migration_mappings,
            "system_settings": existing_system_settings,
            "existing_applications": self.app_storage_resolver.list_application_directories()
        }
        
        return report
    
    def create_missing_settings_with_defaults(self, app_name: str) -> Dict[str, Tuple[bool, str]]:
        """
        Create missing settings files with default values for an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Dict[str, Tuple[bool, str]]: Results for each settings file creation
        """
        results = {}
        
        # Define default settings for each file type
        default_settings = {
            "glue_settings": {
                "Spray Width": 6.0,
                "Spraying Height": 10.0,
                "Fan Speed": 50.0,
                "Generator-Glue Delay": 1,
                "Pump Speed": 10000.0,
                "Pump Reverse Time": 1.0,
                "Pump Speed Reverse": 1000.0,
                "RZ Angle": 0,
                "Glue Type": "Type A",
                "Generator Timeout": 5.0,
                "Time Before Motion": 1.0,
                "Reach Start Threshold": 3.0,
                "Time Before Stop": 1,
                "Reach End Threshold": 1,
                "Initial Ramp Speed": 5000.0,
                "Forward Ramp Steps": 1,
                "Reverse Ramp Steps": 1,
                "Initial Ramp Speed Duration": 0.5,
                "Spray On": false
            },
            "camera_settings": {
                "brightness": 50,
                "contrast": 50,
                "saturation": 50,
                "resolution_width": 640,
                "resolution_height": 480,
                "fps": 30
            },
            "robot_config": {
                "robot_type": "default",
                "max_speed": 100.0,
                "acceleration": 50.0,
                "home_position": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            }
        }
        
        # Check which APPLICATION-SPECIFIC settings files are missing and create them
        # Note: Core settings (camera, robot) are copied from central location, not created as defaults
        settings_types = ["glue_settings", "glue_cell_config"]
        
        for settings_type in settings_types:
            settings_path = self.app_storage_resolver.get_settings_path(
                app_name, settings_type, create_if_missing=True
            )
            
            if not os.path.exists(settings_path):
                try:
                    # Create default settings file
                    default_data = default_settings.get(settings_type, {})
                    
                    # Special handling for glue_cell_config
                    if settings_type == "glue_cell_config":
                        default_data = {
                            "MODE": "production",
                            "PRODUCTION_SERVER_URL": "http://192.168.222.143",
                            "MOCK_SERVER_URL": "http://localhost:5000",
                            "CELL_CONFIG": [
                                {
                                    "id": 1,
                                    "type": "TypeA",
                                    "url": "http://192.168.222.143/cell1",
                                    "zero_offset": 0,
                                    "scale": 1,
                                    "FETCH_TIMEOUT": 5
                                }
                            ]
                        }
                    
                    with open(settings_path, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, indent=4, ensure_ascii=False)
                    
                    results[f"{settings_type}.json"] = (True, f"Created default {settings_type} file")
                    print(f"✅ Created default {settings_type}.json for {app_name}")
                    
                except Exception as e:
                    results[f"{settings_type}.json"] = (False, f"Failed to create {settings_type}: {e}")
                    print(f"❌ Failed to create {settings_type}.json: {e}")
            else:
                results[f"{settings_type}.json"] = (True, f"{settings_type} already exists")
                print(f"ℹ️ {settings_type}.json already exists for {app_name}")
        
        return results
    
    def copy_core_settings_to_applications(self) -> Dict[str, Dict[str, Tuple[bool, str]]]:
        """
        Copy core settings (camera_settings.json, robot_config.json) to all applications.
        
        Returns:
            Dict[str, Dict[str, Tuple[bool, str]]]: Results for each app and setting file
        """
        results = {}
        
        # Get all existing applications
        applications = self.app_storage_resolver.list_application_directories()
        
        for app_name in applications:
            if app_name.startswith('.') or app_name == '__pycache__':
                continue
                
            results[app_name] = {}
            print(f"\n📋 Processing core settings for {app_name}...")
            
            for core_file, settings_type in self.core_settings.items():
                old_file_path = self.old_settings_path / core_file
                new_file_path = self.app_storage_resolver.get_settings_path(
                    app_name, settings_type, create_if_missing=True
                )
                
                try:
                    if old_file_path.exists():
                        # Copy from central location to app location
                        import shutil
                        shutil.copy2(old_file_path, new_file_path)
                        results[app_name][core_file] = (True, f"Copied {core_file} to {app_name}")
                        print(f"   ✅ {core_file} → {app_name}")
                    else:
                        results[app_name][core_file] = (False, f"{core_file} not found in central location")
                        print(f"   ❌ {core_file} not found in central location")
                        
                except Exception as e:
                    results[app_name][core_file] = (False, f"Error copying {core_file}: {e}")
                    print(f"   ❌ Error copying {core_file}: {e}")
        
        return results


def run_migration_interactive():
    """
    Interactive migration runner with user prompts.
    """
    print("=== Settings Migration Tool ===")
    print()
    
    migration_tool = SettingsMigrationTool()
    
    # Generate report
    report = migration_tool.get_migration_report()
    
    print("📊 Migration Report:")
    print(f"   Migration needed: {report['migration_needed']}")
    print(f"   Files to migrate: {report['files_to_migrate']}")
    print(f"   Old settings path: {report['old_settings_path']}")
    print(f"   Existing applications: {report['existing_applications']}")
    
    print("\n🏢 Core Settings (will be copied to each application):")
    for filename, settings_type in migration_tool.core_settings.items():
        old_file_path = migration_tool.old_settings_path / filename
        status = "✅ EXISTS" if old_file_path.exists() else "❌ MISSING"
        print(f"   {filename}: {status} - Required by all applications")
    
    print("\n📱 Application-Specific Settings:")
    for filename, mapping in report['migration_mappings'].items():
        print(f"   {filename} → {mapping['app_name']} only")
    print()
    
    if not report['migration_needed']:
        print("✅ No migration needed!")
        return
    
    # Ask user if they want to proceed
    response = input("Do you want to proceed with migration? (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    # Create application structures
    print("\n🏗️ Creating application structures...")
    app_results = migration_tool.create_application_structures()
    
    # Migrate files
    print("\n📦 Migrating settings files...")
    migration_results = migration_tool.migrate_all_files(backup=True)
    
    # Copy core settings to all applications
    print("\n📋 Copying core settings to all applications...")
    core_results = migration_tool.copy_core_settings_to_applications()
    
    # Create missing settings with defaults
    print("\n🆕 Creating missing settings with defaults...")
    defaults_results = migration_tool.create_missing_settings_with_defaults("glue_dispensing_application")
    
    # Verify migration
    print("\n✅ Verifying migration...")
    verification_successful, verification_results = migration_tool.verify_migration()
    
    if verification_successful:
        print("\n🎉 Migration completed successfully!")
        
        # Ask about cleanup
        cleanup_response = input("\nDo you want to clean up old settings files? (y/N): ").lower().strip()
        if cleanup_response in ['y', 'yes']:
            print("\n🗑️ Cleaning up old files...")
            migration_tool.cleanup_old_files(confirm=True)
    else:
        print("\n❌ Migration verification failed. Please check the errors above.")


if __name__ == "__main__":
    run_migration_interactive()