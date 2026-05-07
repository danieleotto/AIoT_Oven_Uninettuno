class ErroreTimeout(Exception):
    def __init__(self, step:str, elapsed:float, max_time:float) -> None:
        self.step = step
        self.elapsed = elapsed
        self.max_time = max_time
        super().__init__(f"Errore timeout nella fase: {step}")
    
        
class ErroreTemperatura(Exception):
    def __init__(self, step:str, elapsed:float, temp:float, target:float) -> None:
        self.step = step
        self.elapsed = elapsed
        self.temp = temp
        self.target = target
        super().__init__(f"Errore temperatura nella fase: {step}")


class ErroreSonda(Exception):
    def __init__(self) -> None:
        super().__init__(f"Errore lettura sonda.")