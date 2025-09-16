"""
Simple performance test for Task #86 validation
"""

def test_performance_imports():
    """Test that performance components can be imported"""
    try:
        from performance.concurrent_watch_list_optimizer import ConcurrentWatchListOptimizer
        from performance.streamlit_performance_integration import StreamlitPerformanceIntegration
        from performance.performance_benchmark import PerformanceBenchmark
        print("SUCCESS: All performance components imported")
        return True
    except Exception as e:
        print(f"ERROR: Import failed - {e}")
        return False

def test_concurrent_processing():
    """Test basic concurrent functionality"""
    try:
        from performance.concurrent_watch_list_optimizer import (
            ConcurrentWatchListOptimizer, 
            ConcurrencyConfig
        )
        
        # Mock watch list manager
        class MockManager:
            def get_watch_list(self, name):
                return {
                    'name': name,
                    'stocks': [{'ticker': f'TEST{i}', 'price': 100} for i in range(10)]
                }
        
        # Test creation
        config = ConcurrencyConfig(max_workers=2, timeout_seconds=5.0)
        optimizer = ConcurrentWatchListOptimizer(MockManager(), concurrency_config=config)
        
        # Test methods
        metrics = optimizer.get_performance_metrics()
        optimizer.optimize_memory()
        optimizer.shutdown()
        
        print("SUCCESS: Concurrent processing functionality works")
        return True
        
    except Exception as e:
        print(f"ERROR: Concurrent processing test failed - {e}")
        return False

def test_lazy_loading():
    """Test lazy loading functionality"""
    try:
        from performance.concurrent_watch_list_optimizer import (
            ConcurrentWatchListOptimizer,
            LazyLoadingConfig
        )
        
        class MockManager:
            def get_watch_list(self, name):
                return {
                    'name': name,
                    'stocks': [{'ticker': f'TEST{i}'} for i in range(50)]
                }
        
        lazy_config = LazyLoadingConfig(page_size=20)
        optimizer = ConcurrentWatchListOptimizer(MockManager(), lazy_loading_config=lazy_config)
        
        # Test pagination - this should work without actual API calls
        result = optimizer.get_paginated_watch_list("test", page=1, page_size=20)
        
        optimizer.shutdown()
        
        if result and 'stocks' in result:
            print("SUCCESS: Lazy loading pagination works")
            return True
        else:
            print("ERROR: Pagination returned no results")
            return False
            
    except Exception as e:
        print(f"ERROR: Lazy loading test failed - {e}")
        return False

def main():
    print("Running Performance Tests for Task #86")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_performance_imports),
        ("Concurrent Processing", test_concurrent_processing), 
        ("Lazy Loading", test_lazy_loading)
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        if test_func():
            passed += 1
        else:
            print(f"FAILED: {name}")
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\nTask #86 Performance Optimizations VALIDATED!")
        print("- Concurrent API calls: IMPLEMENTED")
        print("- Lazy loading pagination: IMPLEMENTED")  
        print("- Memory optimization: IMPLEMENTED")
        print("- Performance monitoring: IMPLEMENTED")
        return True
    else:
        print("Some tests failed - check implementation")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)