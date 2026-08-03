class Book:
    def __init__(self, title, author):
        
        self.title = title
        self.author = author

    def __str__(self):
       
        return f"书籍:{self.title},作者:{self.author}"


class BookManager:
  
    total_books = 0

    def __init__(self):
        
        self.books = []

    def add_book(self, title, author):
       
        new_book = Book(title, author)
        self.books.append(new_book)
        BookManager.total_books += 1

    def remove_book(self, title):
        
        for book in self.books:
            if book.title == title:
                self.books.remove(book)
                BookManager.total_books -= 1
                break

    def update_book(self, title, new_title=None, new_author=None):
        
        for book in self.books:
            if book.title == title:
                if new_title:
                    book.title = new_title
                if new_author:
                    book.author = new_author
                break

    def list_books(self):
        
        for book in self.books:
            print(book)



if __name__ == "__main__":
   
    manager = BookManager()

    
    print("===============添加书籍===============")
    manager.add_book("Python编程基础", "王健")
    manager.add_book("数据结构", "李冬梅")
    manager.list_books()

    
    print("===============更新与移除书籍===============")
    manager.update_book("Python编程基础", new_title="Python编程基础（项目式微课版）")
    manager.remove_book("数据结构")
    manager.list_books()