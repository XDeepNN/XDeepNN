import yaml
class config:
    def __init__(self):
        self.path='config.yml'
        self.data=self.loadData()
    def loadData(self):
        with open(self.path, encoding='utf-8') as c:
            return yaml.load(c, Loader=yaml.FullLoader)
    def saveData(self):
        with open(self.path, "w", encoding='utf-8') as f:
            yaml.dump(self.data, f)