class Essicatura:
    def __init__(self):
        self.valori = {
            "temperatura": None,
            "durata": None
        }
    
    def completo(self):
        return all(v is not None for v in self.valori.values())
    
    def count(self):
        return sum(v is not None for v in self.valori.values())