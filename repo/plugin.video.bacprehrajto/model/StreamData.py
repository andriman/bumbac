class StreamData(object):
    label: str
    label2: str
    quality: int # height
    path: str
    is_premium: bool

    def __init__(self, label, label2='', quality = 0, path = '', is_premium=False):
        self.label = label
        self.label2 = label2
        self.quality = quality
        self.path = path
        self.is_premium = is_premium
