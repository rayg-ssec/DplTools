
"""
see http://www.doughellmann.com/PyMOTW/abc/

Goals / guiding principles
- each role should have a uniquely named default action verb which is easy to satisfy
- abstract base classes should properly allow interface testing and good errors 
- base class methods that are not abstract should provide truly useful and correct global default implementations
- base classes should NOT be required
- behavior should be more static than dynamic once initialized (overly dynamic = incoherent)
    (if it can crash after initialization, it's broken)
"""
