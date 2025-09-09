import pytest
import time
from pathlib import Path
from PIL import Image
import statistics

from src.utils.image_processor import (
    extract_exif_data,
    extract_exif_with_exifread,
    extract_exif_with_pillow,
    extract_exif_with_pyexiftool
)

@pytest.mark.integration
@pytest.mark.slow
class TestExifExtractionPerformance:
    """Performance benchmarks for EXIF extraction methods"""
    
    def time_function(self, func, *args, **kwargs):
        """Time a function execution"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time
    
    def test_exifread_performance_benchmark(self, test_images):
        """Benchmark exifread extraction performance"""
        times = []
        
        for key, image_path in test_images.items():
            if key == "png_no_exif":  # Skip PNG
                continue
            
            # Run multiple iterations for stable timing
            for _ in range(3):
                _, duration = self.time_function(
                    extract_exif_with_exifread, str(image_path)
                )
                times.append(duration)
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            
            # Log performance metrics
            print(f"\nExifRead Performance:")
            print(f"  Average time: {avg_time:.4f}s")
            print(f"  Median time: {median_time:.4f}s")
            print(f"  Min time: {min(times):.4f}s")
            print(f"  Max time: {max(times):.4f}s")
            
            # Performance assertions (adjust thresholds as needed)
            assert avg_time < 1.0, f"ExifRead too slow: {avg_time:.4f}s average"
            assert max(times) < 2.0, f"ExifRead worst case too slow: {max(times):.4f}s"
    
    def test_pillow_performance_benchmark(self, test_images):
        """Benchmark Pillow extraction performance"""
        times = []
        
        for key, image_path in test_images.items():
            if key == "png_no_exif":
                continue
                
            # Run multiple iterations
            for _ in range(3):
                with Image.open(image_path) as img:
                    _, duration = self.time_function(extract_exif_with_pillow, img)
                    times.append(duration)
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            
            print(f"\nPillow Performance:")
            print(f"  Average time: {avg_time:.4f}s")
            print(f"  Median time: {median_time:.4f}s")
            print(f"  Min time: {min(times):.4f}s") 
            print(f"  Max time: {max(times):.4f}s")
            
            # Pillow should be fast
            assert avg_time < 0.5, f"Pillow too slow: {avg_time:.4f}s average"
    
    @pytest.mark.skipif(
        not hasattr(pytest, 'EXIFTOOL_AVAILABLE') or not pytest.EXIFTOOL_AVAILABLE,
        reason="PyExifTool not available"
    )
    def test_pyexiftool_performance_benchmark(self, test_images):
        """Benchmark PyExifTool extraction performance"""
        times = []
        
        for key, image_path in test_images.items():
            if key == "png_no_exif":
                continue
            
            # Run multiple iterations
            for _ in range(2):  # Fewer iterations since ExifTool can be slower
                _, duration = self.time_function(
                    extract_exif_with_pyexiftool, str(image_path)
                )
                times.append(duration)
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            
            print(f"\nPyExifTool Performance:")
            print(f"  Average time: {avg_time:.4f}s")
            print(f"  Median time: {median_time:.4f}s")
            print(f"  Min time: {min(times):.4f}s")
            print(f"  Max time: {max(times):.4f}s")
            
            # ExifTool can be slower but should be reasonable
            assert avg_time < 3.0, f"PyExifTool too slow: {avg_time:.4f}s average"
    
    def test_multi_library_performance_comparison(self, test_images):
        """Compare performance of multi-library approach vs individual methods"""
        samsung_path = test_images["samsung_s9"]
        
        # Time individual methods
        with Image.open(samsung_path) as img:
            # Pillow method
            _, pillow_time = self.time_function(extract_exif_with_pillow, img)
            
        # ExifRead method  
        _, exifread_time = self.time_function(extract_exif_with_exifread, str(samsung_path))
        
        # Multi-library method (should use primary method - exifread)
        with Image.open(samsung_path) as img:
            _, multi_time = self.time_function(
                extract_exif_data, img, file_path=str(samsung_path)
            )
        
        print(f"\nPerformance Comparison:")
        print(f"  Pillow only: {pillow_time:.4f}s")
        print(f"  ExifRead only: {exifread_time:.4f}s") 
        print(f"  Multi-library: {multi_time:.4f}s")
        
        # Multi-library should be close to the primary method (exifread)
        # Allow some overhead for method selection
        overhead_threshold = exifread_time * 1.5
        assert multi_time <= overhead_threshold, (
            f"Multi-library too slow: {multi_time:.4f}s vs {exifread_time:.4f}s"
        )

@pytest.mark.integration
class TestImageSizePerformance:
    """Test performance across different image sizes"""
    
    def test_large_image_performance(self, test_images):
        """Test performance with larger image files"""
        # Find the largest test image
        largest_image = None
        largest_size = 0
        
        for key, image_path in test_images.items():
            if key == "png_no_exif":
                continue
                
            file_size = image_path.stat().st_size
            if file_size > largest_size:
                largest_size = file_size
                largest_image = image_path
        
        if largest_image:
            print(f"\nTesting largest image: {largest_image.name} ({largest_size/1024/1024:.1f} MB)")
            
            with Image.open(largest_image) as img:
                start_time = time.perf_counter()
                exif_data = extract_exif_data(img, file_path=str(largest_image))
                end_time = time.perf_counter()
                
                duration = end_time - start_time
                print(f"Large image extraction time: {duration:.4f}s")
                
                # Should complete within reasonable time even for large images
                assert duration < 5.0, f"Large image processing too slow: {duration:.4f}s"
                assert isinstance(exif_data, dict)
    
    def test_memory_usage_patterns(self, test_images):
        """Test memory usage doesn't grow excessively with multiple extractions"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple images
        for _ in range(3):  # Process each image multiple times
            for key, image_path in test_images.items():
                if key == "png_no_exif":
                    continue
                
                with Image.open(image_path) as img:
                    exif_data = extract_exif_data(img, file_path=str(image_path))
                    assert isinstance(exif_data, dict)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        print(f"\nMemory usage:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Growth: {memory_growth:.1f} MB")
        
        # Memory growth should be reasonable (adjust threshold as needed)
        assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f} MB"

@pytest.mark.integration
class TestConcurrentExecution:
    """Test EXIF extraction under concurrent execution"""
    
    def test_thread_safety(self, test_images):
        """Basic test that extraction functions don't interfere with each other"""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def extract_worker(image_key, image_path):
            try:
                with Image.open(image_path) as img:
                    exif_data = extract_exif_data(img, file_path=str(image_path))
                    results.put((image_key, len(exif_data)))
            except Exception as e:
                errors.put((image_key, str(e)))
        
        # Start threads for each test image
        threads = []
        valid_images = {k: v for k, v in test_images.items() if k != "png_no_exif"}
        
        for image_key, image_path in valid_images.items():
            thread = threading.Thread(target=extract_worker, args=(image_key, image_path))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10.0)  # 10 second timeout per thread
        
        # Check results
        assert errors.empty(), f"Extraction errors: {list(errors.queue)}"
        assert results.qsize() == len(valid_images), "Not all extractions completed"
        
        # Verify all results are reasonable
        while not results.empty():
            image_key, field_count = results.get()
            assert field_count >= 0, f"Invalid field count for {image_key}: {field_count}"