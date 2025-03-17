import sqlite3
import streamlit as st

class BookCollection:
    def __init__(self):
        """Initialize SQLite database connection and create the books table."""
        self.connection = sqlite3.connect("books.db")  # Local database file
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """Create a table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year TEXT NOT NULL,
                genre TEXT NOT NULL,
                read_status BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        self.connection.commit()

    def create_new_book(self, book_title, book_author, publication_year, book_genre, is_book_read):
        """Add a new book to the SQLite database."""
        self.cursor.execute("""
            INSERT INTO books (title, author, year, genre, read_status)
            VALUES (?, ?, ?, ?, ?)
        """, (book_title, book_author, publication_year, book_genre, is_book_read))
        self.connection.commit()
        st.success("Book added successfully!")

    def delete_book(self, book_title):
        """Remove a book from the database using its title."""
        self.cursor.execute("DELETE FROM books WHERE title = ?", (book_title,))
        self.connection.commit()
        if self.cursor.rowcount:
            st.success("Book removed successfully!")
        else:
            st.error("Book not found!")

    def find_book(self, search_text):
        """Search for books by title or author."""
        self.cursor.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ?",
                            (f"%{search_text}%", f"%{search_text}%"))
        found_books = self.cursor.fetchall()
        return found_books

    def update_book(self, book_id, new_title, new_author, new_year, new_genre, new_read):
        """Modify the details of an existing book in the database."""
        self.cursor.execute("""
            UPDATE books SET title = ?, author = ?, year = ?, genre = ?, read_status = ?
            WHERE id = ?
        """, (new_title, new_author, new_year, new_genre, new_read, book_id))
        self.connection.commit()
        st.success("Book updated successfully!")

    def show_all_books(self):
        """Display all books stored in the SQLite database."""
        self.cursor.execute("SELECT * FROM books")
        books = self.cursor.fetchall()
        return books

    def show_reading_progress(self):
        """Calculate and display statistics about reading progress."""
        self.cursor.execute("SELECT COUNT(*) FROM books")
        total_books = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM books WHERE read_status = 1")
        completed_books = self.cursor.fetchone()[0]

        completion_rate = (completed_books / total_books * 100) if total_books > 0 else 0
        return total_books, completion_rate

    def __del__(self):
        """Close database connection when the object is deleted."""
        self.connection.close()

# Streamlit application
def main():
    st.title("📚 Book Collection Manager 📚")

    book_manager = BookCollection()

    menu = ["Add a new book", "Remove a book", "Search for books", "Update book details", "View all books", "View reading progress"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add a new book":
        st.subheader("Add a new book")
        book_title = st.text_input("Enter book title")
        book_author = st.text_input("Enter author")
        publication_year = st.text_input("Enter publication year")
        book_genre = st.text_input("Enter genre")
        is_book_read = st.radio("Have you read this book?", ("Yes", "No")) == "Yes"
        if st.button("Add Book"):
            book_manager.create_new_book(book_title, book_author, publication_year, book_genre, is_book_read)

    elif choice == "Remove a book":
        st.subheader("Remove a book")
        book_title = st.text_input("Enter the title of the book to remove")
        if st.button("Remove Book"):
            book_manager.delete_book(book_title)

    elif choice == "Search for books":
        st.subheader("Search for books")
        search_text = st.text_input("Enter search term")
        if st.button("Search"):
            found_books = book_manager.find_book(search_text)
            if found_books:
                for book in found_books:
                    reading_status = "Read" if book[5] else "Unread"
                    st.write(f"{book[1]} by {book[2]} ({book[3]}) - {book[4]} - {reading_status}")
            else:
                st.write("No matching books found.")

    elif choice == "Update book details":
        st.subheader("Update book details")
        book_title = st.text_input("Enter the title of the book you want to edit")
        if st.button("Find Book"):
            book_manager.cursor.execute("SELECT * FROM books WHERE title = ?", (book_title,))
            book = book_manager.cursor.fetchone()
            if book:
                new_title = st.text_input("New title", book[1])
                new_author = st.text_input("New author", book[2])
                new_year = st.text_input("New year", book[3])
                new_genre = st.text_input("New genre", book[4])
                new_read = st.radio("Have you read this book?", ("Yes", "No")) == "Yes"
                if st.button("Update Book"):
                    book_manager.update_book(book[0], new_title, new_author, new_year, new_genre, new_read)
            else:
                st.write("Book not found.")

    elif choice == "View all books":
        st.subheader("View all books")
        books = book_manager.show_all_books()
        if books:
            for book in books:
                reading_status = "Read" if book[5] else "Unread"
                st.write(f"{book[1]} by {book[2]} ({book[3]}) - {book[4]} - {reading_status}")
        else:
            st.write("Your collection is empty.")

    elif choice == "View reading progress":
        st.subheader("View reading progress")
        total_books, completion_rate = book_manager.show_reading_progress()
        st.write(f"Total books in collection: {total_books}")
        st.write(f"Reading progress: {completion_rate:.2f}%")

if __name__ == "__main__":
    main()