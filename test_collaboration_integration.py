#!/usr/bin/env python3
"""
Test script for collaboration features integration
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_collaboration_imports():
    """Test that all collaboration modules can be imported correctly"""
    try:
        # Test core collaboration modules
        from core.collaboration.collaboration_manager import CollaborationManager
        from core.collaboration.analysis_sharing import AnalysisShareManager
        from core.collaboration.annotations import AnnotationManager
        from core.collaboration.shared_workspaces import WorkspaceManager
        from core.collaboration.realtime_collaboration import RealtimeCollaborationManager

        logger.info("✅ Core collaboration modules imported successfully")

        # Test UI modules
        from ui.streamlit.collaboration_ui import render_collaboration_dashboard, init_collaboration_session

        logger.info("✅ Collaboration UI modules imported successfully")

        # Test main app integration
        from ui.streamlit.fcf_analysis_streamlit import initialize_collaboration_for_analysis, share_analysis_result

        logger.info("✅ Main app integration functions imported successfully")

        return True

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_collaboration_manager_basic():
    """Test basic collaboration manager functionality"""
    try:
        from core.collaboration.collaboration_manager import CollaborationManager
        from core.user_preferences.user_profile import create_default_user_profile

        # Create collaboration manager
        collab_manager = CollaborationManager()
        logger.info("✅ CollaborationManager created successfully")

        # Create test user profile
        user_profile = create_default_user_profile(
            user_id="test_user_123",
            username="test_user",
            email="test@example.com"
        )
        logger.info("✅ Test user profile created successfully")

        # Test analysis sharing
        test_analysis_data = {
            "analysis_id": "test_analysis_001",
            "ticker": "TEST",
            "company_name": "Test Company",
            "analysis_date": "2025-09-23",
            "results": {"test_metric": 100},
            "key_metrics": {"revenue": 1000000}
        }

        shared_analysis = collab_manager.create_analysis_share(
            analysis_data=test_analysis_data,
            user_profile=user_profile,
            title="Test Analysis Share",
            description="This is a test analysis for collaboration testing"
        )

        logger.info(f"✅ Analysis share created successfully: {shared_analysis.share_id}")

        # Test accessing the share
        collaboration_context = collab_manager.access_shared_analysis(
            share_id=shared_analysis.share_id,
            user_profile=user_profile
        )

        if collaboration_context:
            logger.info("✅ Analysis share accessed successfully")
        else:
            logger.error("❌ Failed to access analysis share")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Collaboration manager test failed: {e}")
        return False

def test_realtime_collaboration():
    """Test real-time collaboration features"""
    try:
        from core.collaboration.realtime_collaboration import get_realtime_manager, join_analysis_collaboration

        # Get realtime manager
        rt_manager = get_realtime_manager()
        logger.info("✅ Realtime collaboration manager obtained")

        # Test joining a collaboration room
        room = join_analysis_collaboration(
            analysis_id="test_analysis_001",
            user_id="test_user_123",
            username="test_user",
            session_id="test_session_456"
        )

        if room:
            logger.info(f"✅ Joined collaboration room: {room.room_id}")

            # Test room state
            room_state = rt_manager.get_room_state("test_analysis_001")
            if room_state:
                logger.info(f"✅ Room state retrieved: {room_state['user_count']} users")
            else:
                logger.warning("⚠️ Could not retrieve room state")

        else:
            logger.error("❌ Failed to join collaboration room")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Realtime collaboration test failed: {e}")
        return False

def main():
    """Run all collaboration integration tests"""
    logger.info("🚀 Starting collaboration integration tests...")

    tests = [
        ("Import Tests", test_collaboration_imports),
        ("Collaboration Manager Tests", test_collaboration_manager_basic),
        ("Realtime Collaboration Tests", test_realtime_collaboration)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name}...")

        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1

    logger.info(f"\n🏁 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        logger.info("🎉 All collaboration integration tests passed!")
        return True
    else:
        logger.error("💥 Some tests failed. Check logs for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)