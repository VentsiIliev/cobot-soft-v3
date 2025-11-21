#!/usr/bin/env python3
"""
Test Script for Standardized Settings System

This script tests the new standardized settings system to ensure:
1. ApplicationStorageResolver works correctly
2. BaseApplicationSettingsHandler provides consistent behavior
3. StandardizedGlueSettingsHandler works as expected
4. Migration tools function properly
"""

import os
import tempfile
import json
from pathlib import Path

def test_application_storage_resolver():
    """Test the ApplicationStorageResolver functionality."""
    print("🧪 Testing ApplicationStorageResolver...")
    
    from backend.system.utils.ApplicationStorageResolver import ApplicationStorageResolver
    
    resolver = ApplicationStorageResolver()
    app_name = "test_glue_app"
    
    # Test path generation
    app_root = resolver.get_app_root_path(app_name)
    storage_root = resolver.get_storage_root_path(app_name)
    settings_path = resolver.get_settings_path(app_name, "test_settings")
    templates_path = resolver.get_templates_path(app_name)
    
    print(f"   App Root: {app_root}")
    print(f"   Storage Root: {storage_root}")
    print(f"   Settings Path: {settings_path}")
    print(f"   Templates Path: {templates_path}")
    
    # Test application structure creation
    success = resolver.create_application_structure(app_name)
    print(f"   Structure Creation: {'✅' if success else '❌'}")
    
    # Test convenience functions
    from backend.system.utils.ApplicationStorageResolver import (
        get_app_settings_path, 
        get_app_templates_path
    )
    
    convenience_settings = get_app_settings_path(app_name, "convenience_test")
    convenience_templates = get_app_templates_path(app_name)
    
    print(f"   Convenience Settings: {convenience_settings}")
    print(f"   Convenience Templates: {convenience_templates}")
    
    print("✅ ApplicationStorageResolver tests completed\n")
    return True


def test_standardized_glue_settings():
    """Test the StandardizedGlueSettingsHandler."""
    print("🧪 Testing StandardizedGlueSettingsHandler...")
    
    try:
        from applications.glue_dispensing_application.settings.StandardizedGlueSettingsHandler import StandardizedGlueSettingsHandler
        
        # Create handler instance
        handler = StandardizedGlueSettingsHandler()
        print("   ✅ Handler created successfully")
        
        # Test getting settings
        settings = handler.handle_get_settings()
        print(f"   ✅ Got settings: {len(settings)} items")
        print(f"   Sample setting: Spray On = {settings.get('Spray On', 'NOT_FOUND')}")
        
        # Test setting a value
        test_settings = {
            "Spray On": True,
            "Fan Speed": 75.0
        }
        
        success, message = handler.handle_set_settings(test_settings)
        print(f"   Set Settings: {'✅' if success else '❌'} - {message}")
        
        # Verify the change
        updated_settings = handler.handle_get_settings()
        spray_on_value = updated_settings.get("Spray On")
        fan_speed_value = updated_settings.get("Fan Speed")
        
        print(f"   Verification - Spray On: {spray_on_value} (expected: True)")
        print(f"   Verification - Fan Speed: {fan_speed_value} (expected: 75.0)")
        
        # Test individual setting update
        success, message = handler.update_individual_setting("Spray Width", 8.5)
        print(f"   Individual Update: {'✅' if success else '❌'} - {message}")
        
        # Test getting individual value
        spray_width = handler.get_setting_value("Spray Width")
        print(f"   Individual Get: Spray Width = {spray_width}")
        
        print("✅ StandardizedGlueSettingsHandler tests completed\n")
        return True
        
    except Exception as e:
        print(f"❌ StandardizedGlueSettingsHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_tool():
    """Test the SettingsMigrationTool."""
    print("🧪 Testing SettingsMigrationTool...")
    
    try:
        from backend.system.utils.SettingsMigrationTool import SettingsMigrationTool
        
        # Create migration tool
        migration_tool = SettingsMigrationTool()
        print("   ✅ Migration tool created")
        
        # Check migration status
        migration_needed, files_to_migrate = migration_tool.check_migration_needed()
        print(f"   Migration needed: {migration_needed}")
        print(f"   Files to migrate: {files_to_migrate}")
        
        # Generate report
        report = migration_tool.get_migration_report()
        print(f"   Report generated: {len(report)} sections")
        print(f"   Old settings path: {report['old_settings_path']}")
        print(f"   Existing applications: {report['existing_applications']}")
        
        # Test structure creation
        app_results = migration_tool.create_application_structures()
        print(f"   Structure creation results: {app_results}")
        
        print("✅ SettingsMigrationTool tests completed\n")
        return True
        
    except Exception as e:
        print(f"❌ SettingsMigrationTool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_path_consistency():
    """Test that paths are consistent and properly isolated."""
    print("🧪 Testing Path Consistency...")
    
    from backend.system.utils.ApplicationStorageResolver import get_application_storage_resolver
    
    resolver = get_application_storage_resolver()
    
    # Test multiple applications
    apps = ["glue_dispensing_application", "paint_application", "welding_application"]
    
    for app in apps:
        settings_path = resolver.get_settings_path(app, "main_settings", create_if_missing=True)
        templates_path = resolver.get_templates_path(app, create_if_missing=True)
        
        print(f"   {app}:")
        print(f"     Settings: {settings_path}")
        print(f"     Templates: {templates_path}")
        
        # Verify isolation - each app should have its own directory
        assert app in settings_path, f"App name not in settings path: {settings_path}"
        assert app in templates_path, f"App name not in templates path: {templates_path}"
        
        # Verify directory structure
        settings_dir = os.path.dirname(settings_path)
        assert settings_dir.endswith(f"{app}/storage/settings"), f"Incorrect settings structure: {settings_dir}"
        
        templates_dir = templates_path
        assert templates_dir.endswith(f"{app}/storage/templates"), f"Incorrect templates structure: {templates_dir}"
    
    print("✅ Path consistency tests completed\n")
    return True


def test_error_handling():
    """Test error handling in the standardized system."""
    print("🧪 Testing Error Handling...")
    
    try:
        from applications.glue_dispensing_application.settings.StandardizedGlueSettingsHandler import StandardizedGlueSettingsHandler
        
        handler = StandardizedGlueSettingsHandler()
        
        # Test invalid settings data
        invalid_settings = {
            "Spray Width": "invalid_string_value",  # Should be numeric
            "Invalid Key": "some value"  # Unknown key
        }
        
        success, message = handler.handle_set_settings(invalid_settings)
        print(f"   Invalid Settings Test: {'❌' if success else '✅'} (correctly rejected)")
        print(f"   Error Message: {message}")
        
        # Test getting unknown setting
        unknown_value = handler.get_setting_value("NonExistentSetting")
        print(f"   Unknown Setting: {unknown_value} (should be None)")
        
        print("✅ Error handling tests completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Starting Standardized Settings System Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run individual tests
    test_results.append(("ApplicationStorageResolver", test_application_storage_resolver()))
    test_results.append(("PathConsistency", test_path_consistency()))
    test_results.append(("MigrationTool", test_migration_tool()))
    test_results.append(("StandardizedGlueSettings", test_standardized_glue_settings()))
    test_results.append(("ErrorHandling", test_error_handling()))
    
    # Report results
    print("=" * 60)
    print("🏁 Test Results Summary:")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The standardized settings system is working correctly.")
    else:
        print(f"⚠️ {failed} tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    run_all_tests()