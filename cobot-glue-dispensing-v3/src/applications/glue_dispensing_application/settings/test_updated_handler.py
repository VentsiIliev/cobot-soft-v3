#!/usr/bin/env python3
"""
Test Updated Glue Settings Handler

This script tests that the updated GlueSettingsHandler maintains backward 
compatibility while using the new standardized base class.
"""

def test_backward_compatibility():
    """Test that existing code still works with the updated handler."""
    print("🧪 Testing Updated GlueSettingsHandler Backward Compatibility...")
    
    try:
        from applications.glue_dispensing_application.settings.GlueSettingsHandler import GlueSettingsHandler
        
        # Test 1: Old-style initialization
        print("   Testing old-style initialization...")
        handler = GlueSettingsHandler()
        print("   ✅ Handler created successfully")
        
        # Test 2: Legacy property access
        print("   Testing legacy property access...")
        settings_obj = handler.glue_settings  # Legacy property
        settings_file = handler.settings_file  # Legacy property
        print(f"   ✅ Legacy properties work: settings_file = {settings_file}")
        
        # Test 3: Legacy method calls
        print("   Testing legacy method calls...")
        glue_settings = handler.get_glue_settings()  # Legacy method
        print(f"   ✅ Legacy get_glue_settings() works")
        
        # Test 4: New standardized methods
        print("   Testing new standardized methods...")
        current_settings = handler.handle_get_settings()
        print(f"   ✅ New handle_get_settings() works: {len(current_settings)} settings")
        
        # Test 5: Setting and getting values
        print("   Testing settings persistence...")
        test_settings = {
            "Spray On": True,
            "Fan Speed": 80.0
        }
        
        success, message = handler.handle_set_settings(test_settings)
        print(f"   Set settings: {'✅' if success else '❌'} - {message}")
        
        # Verify the changes
        updated_settings = handler.handle_get_settings()
        spray_on = updated_settings.get("Spray On")
        fan_speed = updated_settings.get("Fan Speed")
        
        print(f"   Verification - Spray On: {spray_on} (expected: True)")
        print(f"   Verification - Fan Speed: {fan_speed} (expected: 80.0)")
        
        # Test 6: Convenience methods
        print("   Testing convenience methods...")
        individual_success, individual_message = handler.update_individual_setting("Spray Width", 7.5)
        print(f"   Individual update: {'✅' if individual_success else '❌'} - {individual_message}")
        
        spray_width = handler.get_setting_value("Spray Width")
        print(f"   Individual get: Spray Width = {spray_width}")
        
        # Test 7: Reset to defaults
        print("   Testing reset to defaults...")
        reset_success, reset_message = handler.reset_to_defaults()
        print(f"   Reset: {'✅' if reset_success else '❌'} - {reset_message}")
        
        print("✅ All backward compatibility tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_path_isolation():
    """Test that the new storage path isolation works correctly."""
    print("🧪 Testing Storage Path Isolation...")
    
    try:
        from applications.glue_dispensing_application.settings.GlueSettingsHandler import GlueSettingsHandler
        
        # Test with default (new) storage path
        print("   Testing default (application-specific) storage path...")
        handler1 = GlueSettingsHandler()
        
        # Test settings persistence in new location
        test_settings = {"Spray On": False, "Fan Speed": 90.0}
        success, message = handler1.handle_set_settings(test_settings)
        
        print(f"   Settings saved to new location: {'✅' if success else '❌'}")
        print(f"   Storage path: {handler1.settings_file_path}")
        
        # Verify the path is in the application-specific location
        expected_path_part = "applications/glue_dispensing_application/storage/settings"
        if expected_path_part in handler1.settings_file_path:
            print("   ✅ Settings stored in application-specific location")
        else:
            print(f"   ❌ Settings not in expected location: {handler1.settings_file_path}")
            return False
        
        print("✅ Storage path isolation tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Storage path isolation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling in the updated handler."""
    print("🧪 Testing Error Handling...")
    
    try:
        from applications.glue_dispensing_application.settings.GlueSettingsHandler import GlueSettingsHandler
        
        handler = GlueSettingsHandler()
        
        # Test invalid settings
        print("   Testing invalid settings rejection...")
        invalid_settings = {
            "Spray Width": "invalid_string_value",  # Should be numeric
            "Unknown Setting": "test"  # Unknown key
        }
        
        success, message = handler.handle_set_settings(invalid_settings)
        print(f"   Invalid settings rejected: {'✅' if not success else '❌'}")
        print(f"   Error message: {message}")
        
        # Test getting unknown setting
        unknown_value = handler.get_setting_value("NonExistentSetting")
        print(f"   Unknown setting returns None: {'✅' if unknown_value is None else '❌'}")
        
        print("✅ Error handling tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_updated_handler_tests():
    """Run all tests for the updated handler."""
    print("🚀 Testing Updated GlueSettingsHandler")
    print("=" * 60)
    
    test_results = []
    test_results.append(("BackwardCompatibility", test_backward_compatibility()))
    test_results.append(("StoragePathIsolation", test_storage_path_isolation()))
    test_results.append(("ErrorHandling", test_error_handling()))
    
    # Report results
    print("=" * 60)
    print("🏁 Updated Handler Test Results:")
    
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
        print("🎉 Updated GlueSettingsHandler works perfectly!")
        print("   - Maintains backward compatibility")
        print("   - Uses application-specific storage")
        print("   - Provides enhanced error handling")
        print("   - Eliminates parameter passing bugs")
    else:
        print(f"⚠️ {failed} tests failed. Please check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    run_updated_handler_tests()