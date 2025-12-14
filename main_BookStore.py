from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title='Book Store API')
class Book(BaseModel):
    name: str
    stock: int

# penyimpanan sementara (in-memory)
books = []
@app.post("/books", summary = "Tambah buku baru")
def add_book(book:Book):
    #cek buku apakah ada
    for b in books:
        if b.name.lower() == book.name.lower():
            raise HTTPException(status_code=400, detail='Book already exists')
    books.append(book)
    return {'message': "Book added", "book": book}


@app.get("/books", summary='Lihat semua buku')
def get_all_books():
    return {"books": books}

@app.get("books/{book_name}", summary='Cari buku berdasar nama')
def get_book(book_name:str):
    for b in books:
        if b.name.lower() == book_name.lower():
            return b
    raise HTTPException(status_code=404, detail="Book not found")

