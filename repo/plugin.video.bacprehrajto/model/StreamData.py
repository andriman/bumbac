class StreamData(object):
    label: str
    quality: int # height
    path: str

    def __init__(self, label, quality, path):
        self.label = label
        self.quality = quality
        self.path = path
