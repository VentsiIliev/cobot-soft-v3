"""
Performance optimization utilities for the state machine framework.

This module provides performance monitoring, optimization strategies, and
profiling tools to improve state machine execution efficiency.
"""

import time
import threading
import weakref
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Tuple
from collections import deque, defaultdict
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor
import gc


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring system performance."""
    
    # Timing metrics
    total_runtime: float = 0.0
    average_event_processing_time: float = 0.0
    peak_event_processing_time: float = 0.0
    
    # Throughput metrics
    events_processed: int = 0
    events_per_second: float = 0.0
    transitions_per_second: float = 0.0
    
    # Resource metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    thread_count: int = 0
    
    # Queue metrics
    queue_size: int = 0
    max_queue_size: int = 0
    queue_wait_time: float = 0.0
    
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_ratio: float = 0.0
    
    # Error metrics
    errors_per_second: float = 0.0
    recovery_time: float = 0.0
    
    @property
    def cache_efficiency(self) -> float:
        """Calculate cache efficiency percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


class PerformanceProfiler:
    """Profiler for measuring execution performance."""
    
    def __init__(self, max_samples: int = 10000):
        """
        Initialize profiler.
        
        Args:
            max_samples: Maximum number of performance samples to keep
        """
        self.max_samples = max_samples
        self._samples: deque = deque(maxlen=max_samples)
        self._method_timings: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        self._start_time = time.time()
        self._active_measurements: Dict[str, float] = {}
        
    def start_measurement(self, operation: str) -> str:
        """
        Start measuring an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Measurement ID for ending the measurement
        """
        measurement_id = f"{operation}_{time.time()}_{id(self)}"
        with self._lock:
            self._active_measurements[measurement_id] = time.time()
        return measurement_id
    
    def end_measurement(self, measurement_id: str) -> Optional[float]:
        """
        End a measurement and return the duration.
        
        Args:
            measurement_id: Measurement ID from start_measurement
            
        Returns:
            Duration in seconds or None if measurement not found
        """
        with self._lock:
            start_time = self._active_measurements.pop(measurement_id, None)
            if start_time:
                duration = time.time() - start_time
                operation = measurement_id.split('_')[0]
                self._method_timings[operation].append(duration)
                
                # Keep only recent timings to prevent memory growth
                if len(self._method_timings[operation]) > 1000:
                    self._method_timings[operation] = self._method_timings[operation][-500:]
                
                return duration
        return None
    
    def measure(self, operation: str):
        """
        Decorator for measuring method execution time.
        
        Args:
            operation: Operation name
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                measurement_id = self.start_measurement(operation)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.end_measurement(measurement_id)
            return wrapper
        return decorator
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            summary = {}
            
            for operation, timings in self._method_timings.items():
                if timings:
                    summary[operation] = {
                        'call_count': len(timings),
                        'total_time': sum(timings),
                        'average_time': sum(timings) / len(timings),
                        'min_time': min(timings),
                        'max_time': max(timings),
                        'calls_per_second': len(timings) / (time.time() - self._start_time)
                    }
            
            return {
                'operations': summary,
                'total_operations': sum(len(timings) for timings in self._method_timings.values()),
                'profiling_duration': time.time() - self._start_time,
                'active_measurements': len(self._active_measurements)
            }


class PerformanceOptimizer:
    """Performance optimization strategies and utilities."""
    
    def __init__(self):
        """Initialize performance optimizer."""
        self._cache_strategies = {}
        self._optimization_flags = {
            'enable_caching': True,
            'enable_lazy_loading': True,
            'enable_gc_optimization': True,
            'enable_thread_pool_optimization': True
        }
        self._cache_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
        self._lock = threading.RLock()
    
    def create_lru_cache(self, maxsize: int = 128):
        """
        Create an LRU cache with performance tracking.
        
        Args:
            maxsize: Maximum cache size
            
        Returns:
            Cache decorator function
        """
        from functools import lru_cache
        
        def cache_decorator(func):
            # Create LRU cache
            cached_func = lru_cache(maxsize=maxsize)(func)
            original_func = func
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}_{hash((args, tuple(sorted(kwargs.items()))))}"
                
                try:
                    result = cached_func(*args, **kwargs)
                    with self._lock:
                        self._cache_stats[func.__name__]['hits'] += 1
                    return result
                except:
                    with self._lock:
                        self._cache_stats[func.__name__]['misses'] += 1
                    return original_func(*args, **kwargs)
            
            # Expose cache info
            wrapper.cache_info = cached_func.cache_info
            wrapper.cache_clear = cached_func.cache_clear
            
            return wrapper
        
        return cache_decorator
    
    def lazy_property(self, func):
        """
        Lazy property decorator for expensive computations.
        
        Args:
            func: Property function
            
        Returns:
            Lazy property
        """
        attr_name = f'_lazy_{func.__name__}'
        
        @property
        @wraps(func)
        def wrapper(self):
            if not hasattr(self, attr_name):
                setattr(self, attr_name, func(self))
            return getattr(self, attr_name)
        
        return wrapper
    
    def batch_processor(self, batch_size: int = 100, timeout: float = 1.0):
        """
        Batch processor decorator for optimizing bulk operations.
        
        Args:
            batch_size: Maximum batch size
            timeout: Maximum wait time for batch completion
            
        Returns:
            Batch processing decorator
        """
        def decorator(func):
            batch_queue = deque()
            batch_lock = threading.Lock()
            last_process_time = time.time()
            
            def process_batch():
                nonlocal last_process_time
                with batch_lock:
                    if not batch_queue:
                        return
                    
                    batch = list(batch_queue)
                    batch_queue.clear()
                    last_process_time = time.time()
                
                # Process batch
                if batch:
                    func(batch)
            
            def batch_wrapper(item):
                with batch_lock:
                    batch_queue.append(item)
                    
                    # Process if batch is full or timeout reached
                    should_process = (
                        len(batch_queue) >= batch_size or
                        (time.time() - last_process_time) > timeout
                    )
                
                if should_process:
                    process_batch()
            
            return batch_wrapper
        
        return decorator
    
    def optimize_garbage_collection(self):
        """Optimize garbage collection settings."""
        if self._optimization_flags['enable_gc_optimization']:
            import gc
            
            # Tune garbage collection thresholds for better performance
            gc.set_threshold(700, 10, 10)  # More aggressive collection
            
            # Force a collection to start clean
            gc.collect()
    
    def create_optimized_thread_pool(self, max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """
        Create an optimized thread pool.
        
        Args:
            max_workers: Maximum number of worker threads
            
        Returns:
            Optimized thread pool executor
        """
        if max_workers is None:
            import os
            max_workers = min(32, (os.cpu_count() or 1) + 4)
        
        return ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix='StateMachine-Worker-'
        )
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            stats = {}
            total_hits = 0
            total_misses = 0
            
            for func_name, cache_stats in self._cache_stats.items():
                hits = cache_stats['hits']
                misses = cache_stats['misses']
                total = hits + misses
                
                stats[func_name] = {
                    'hits': hits,
                    'misses': misses,
                    'hit_ratio': (hits / total * 100) if total > 0 else 0.0
                }
                
                total_hits += hits
                total_misses += misses
            
            total_requests = total_hits + total_misses
            overall_hit_ratio = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                'function_stats': stats,
                'overall': {
                    'total_hits': total_hits,
                    'total_misses': total_misses,
                    'hit_ratio': overall_hit_ratio
                }
            }


class ResourceMonitor:
    """Monitor system resource usage."""
    
    def __init__(self, sampling_interval: float = 1.0):
        """
        Initialize resource monitor.
        
        Args:
            sampling_interval: Resource sampling interval in seconds
        """
        self.sampling_interval = sampling_interval
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._resource_history: deque = deque(maxlen=3600)  # Keep 1 hour of samples
        self._lock = threading.RLock()
        
    def start_monitoring(self):
        """Start resource monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True,
            name="ResourceMonitor"
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
    
    def _monitor_resources(self):
        """Monitor system resources."""
        import psutil
        import threading
        
        process = psutil.Process()
        
        while self._monitoring:
            try:
                # Get resource usage
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                thread_count = process.num_threads()
                
                resource_sample = {
                    'timestamp': time.time(),
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'cpu_percent': cpu_percent,
                    'thread_count': thread_count,
                    'active_thread_count': threading.active_count()
                }
                
                with self._lock:
                    self._resource_history.append(resource_sample)
                
                time.sleep(self.sampling_interval)
                
            except Exception as e:
                print(f"Error monitoring resources: {e}")
                time.sleep(self.sampling_interval)
    
    def get_current_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        with self._lock:
            if self._resource_history:
                return dict(self._resource_history[-1])
            return {}
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get resource usage summary."""
        with self._lock:
            if not self._resource_history:
                return {}
            
            samples = list(self._resource_history)
            
            # Calculate averages and peaks
            memory_values = [s['memory_mb'] for s in samples]
            cpu_values = [s['cpu_percent'] for s in samples]
            thread_values = [s['thread_count'] for s in samples]
            
            return {
                'sample_count': len(samples),
                'monitoring_duration': samples[-1]['timestamp'] - samples[0]['timestamp'],
                'memory': {
                    'current_mb': memory_values[-1],
                    'average_mb': sum(memory_values) / len(memory_values),
                    'peak_mb': max(memory_values),
                    'min_mb': min(memory_values)
                },
                'cpu': {
                    'current_percent': cpu_values[-1],
                    'average_percent': sum(cpu_values) / len(cpu_values),
                    'peak_percent': max(cpu_values)
                },
                'threads': {
                    'current_count': thread_values[-1],
                    'average_count': sum(thread_values) / len(thread_values),
                    'peak_count': max(thread_values)
                }
            }


class PerformanceManager:
    """Comprehensive performance management for state machines."""
    
    def __init__(self):
        """Initialize performance manager."""
        self.profiler = PerformanceProfiler()
        self.optimizer = PerformanceOptimizer()
        self.resource_monitor = ResourceMonitor()
        self._performance_callbacks: List[Callable[[Dict[str, Any]], None]] = []
    
    def add_performance_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add performance monitoring callback."""
        self._performance_callbacks.append(callback)
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'profiler': self.profiler.get_performance_summary(),
            'cache': self.optimizer.get_cache_statistics(),
            'resources': self.resource_monitor.get_usage_summary(),
            'timestamp': time.time()
        }
    
    def start_monitoring(self):
        """Start all monitoring components."""
        self.resource_monitor.start_monitoring()
        self.optimizer.optimize_garbage_collection()
    
    def stop_monitoring(self):
        """Stop all monitoring components."""
        self.resource_monitor.stop_monitoring()
    
    def notify_performance_callbacks(self, performance_data: Dict[str, Any]):
        """Notify all performance callbacks."""
        for callback in self._performance_callbacks:
            try:
                callback(performance_data)
            except Exception as e:
                print(f"Error in performance callback: {e}")