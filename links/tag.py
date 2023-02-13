class Tag():
    links = []
    
    def __init__(self, name: str, link: str) -> None:
        self.name = name
        self.links.append(link)