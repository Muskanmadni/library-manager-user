import sqlite3
import streamlit as st
import hashlib

# Setup Streamlit UI
st.set_page_config(page_title="📚 Library Manager", layout="wide")

# Database setup for users
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")
conn.commit()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User Authentication Class
class UserAuth:
    @staticmethod
    def register_user(name, email, password):
        hashed_password = hash_password(password)
        try:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def login_user(email, password):
        hashed_password = hash_password(password)
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed_password))
        return cursor.fetchone()

# User-Specific Book Collection
class BookCollection:
    def __init__(self, user_email):
        db_name = f"books_{hashlib.md5(user_email.encode()).hexdigest()}.db"
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
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

    def create_new_book(self, title, author, year, genre, read_status):
        self.cursor.execute("""
            INSERT INTO books (title, author, year, genre, read_status)
            VALUES (?, ?, ?, ?, ?)
        """, (title, author, year, genre, read_status))
        self.connection.commit()
        st.success("✅ Book added successfully!")

    def delete_book(self, title):
        self.cursor.execute("DELETE FROM books WHERE title = ?", (title,))
        self.connection.commit()
        if self.cursor.rowcount:
            st.success("🗑 Book removed successfully!")
        else:
            st.error("⚠️ Book not found!")

    def show_all_books(self):
        self.cursor.execute("SELECT * FROM books")
        return self.cursor.fetchall()

    def show_reading_progress(self):
        self.cursor.execute("SELECT COUNT(*) FROM books")
        total_books = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM books WHERE read_status = 1")
        completed_books = self.cursor.fetchone()[0]
        return total_books, (completed_books / total_books * 100) if total_books else 0

# Streamlit App
def main():
    st.markdown("<h1 style='text-align: center;'>📚 Library Manager</h1>", unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = None

    # **User Login & Registration**
    if not st.session_state["logged_in"]:
        tab_login, tab_register = st.tabs(["🔑 Login", "🆕 Register"])

        with tab_login:
            st.subheader("🔹 Login")
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")
            if st.button("Login"):
                user = UserAuth.login_user(email, password)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = email
                    st.rerun()
                else:
                    st.error("⚠️ Invalid email or password!")

        with tab_register:
            st.subheader("🔹 Register")
            name = st.text_input("👤 Name")
            email = st.text_input("📧 Email" , key="login_email")
            password = st.text_input("🔑 Password", type="password" , key="password")
            if st.button("Register" , key="register"):
                if UserAuth.register_user(name, email, password):
                    st.success("🎉 Registration successful! Please log in.")
                else:
                    st.error("⚠️ Email already registered!")
        return

    # **If Logged In, Show Library**
    book_manager = BookCollection(st.session_state["user_email"])
    total_books, completion_rate = book_manager.show_reading_progress()

    # **Display Reading Progress**
    st.markdown(f"📚 **Total Books:** {total_books}")
    st.progress(completion_rate / 100)
    st.markdown(f"✅ **Reading Progress:** {completion_rate:.2f}%")

    # **Tabs for Book Management**
    tab1, tab2, tab3 = st.tabs(["📖 View Books", "➕ Add Book", "🔍 Search & Remove"])

    with tab1:
        st.subheader("📚 My Book Collection")
        books = book_manager.show_all_books()
        if books:
            cols = st.columns(3)
            for index, book in enumerate(books):
                with cols[index % 3]:
                    st.markdown(f"""
                    <div style="border:2px solid #ddd; padding:10px; border-radius:10px; background-color:#f9f9f9;">
                        <h4>{book[1]}</h4>
                        <p><strong>📖 Author:</strong> {book[2]}</p>
                        <p><strong>📅 Year:</strong> {book[3]}</p>
                        <p><strong>📌 Genre:</strong> {book[4]}</p>
                        <p><strong>📗 Status:</strong> {"✅ Read" if book[5] else "❌ Unread"}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📂 No books added yet.")

    with tab2:
        st.subheader("➕ Add a New Book")
        title = st.text_input("📖 Book Title")
        author = st.text_input("👤 Author")
        year = st.text_input("📅 Year")
        genre = st.text_input("📌 Genre")
        read_status = st.radio("📗 Have you read this book?", ["No", "Yes"]) == "Yes"
        if st.button("Add Book"):
            book_manager.create_new_book(title, author, year, genre, read_status)

    with tab3:
        st.subheader("🔍 Search & Remove Books")
        search_text = st.text_input("🔍 Search by Title or Author")
        if st.button("Search"):
            found_books = book_manager.show_all_books()
            for book in found_books:
                if search_text.lower() in book[1].lower() or search_text.lower() in book[2].lower():
                    st.write(f"{book[1]} by {book[2]} ({book[3]}) - {book[4]} - {'✅ Read' if book[5] else '❌ Unread'}")
        remove_title = st.text_input("🗑 Enter Book Title to Remove")
        if st.button("Remove Book"):
            book_manager.delete_book(remove_title)

    # **Logout Button**
    if st.button("🚪 Logout", key="logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = None
        st.rerun()

if __name__ == "__main__":
    main()
