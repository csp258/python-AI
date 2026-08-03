class Star:
 
    def __init__(self, name, movie):
        self.name = name
        self.movie = movie
    
   
    def playing(self):
        print(f"{self.name}出演了《{self.movie}》,非常好看！")


star = Star("周星驰", "大话西游")

star.playing()