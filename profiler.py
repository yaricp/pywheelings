import hotshot
import cProfile


def profile_hot(func):
    """Decorator for run function profile"""
    def wrapper(*args, **kwargs):
        profile_filename = func.__name__ + '.prof'
        profiler = hotshot.Profile(profile_filename)
        profiler.start()
        result = func(*args, **kwargs)
        profiler.stop()
        profiler.close()
        return result
    return wrapper
    

def profile_c(func):
    """Decorator for run function profile"""
    def wrapper(*args, **kwargs):
        print 'prf'+func.__name__
        profile_filename = func.__name__ + '1.prof'
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(profile_filename)
        return result
    return wrapper
