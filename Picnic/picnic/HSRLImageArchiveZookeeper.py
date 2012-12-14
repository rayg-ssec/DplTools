import dplkit.role.zookeeper

class HSRLImageArchiveZookeeper(dplkit.role.zookeeper.aZookeeper):
    def __init__(self):
        super(HSRLImageArchiveZookeeper,self).__init__()

    def open(self,uri):
        #return netcdf structure with metaframe
        return uri

    def obtain(self,uri, *args, **kwargs):
        return uri
