Vue.createApp({
            data() {
                return {
                    books: [],
                    searchTerm: '',
                    liveTime: '',
                };
            },
            computed: {
                filteredBooks() {
                    if (!this.searchTerm) return this.books;

                    return this.books.filter(book => {
                        return (
                            book.title.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                            book.user_id.toLowerCase().includes(this.searchTerm.toLowerCase())
                        );
                    });
                }
            },
            created() {
                this.updateTime();  // Initialize the time
                setInterval(this.updateTime, 1000);  // Update the time every second
            },
            mounted() {
                this.fetchAllocatedBooks();
                this.setupLogoutListener();
            },
            methods: {
                updateTime() {
                    const now = new Date();
                    this.liveTime = now.toLocaleTimeString();  // Formats the time according to the locale
                },
                setupLogoutListener() {
                    document.getElementById('logoutButton').addEventListener('click', () => {
                        localStorage.removeItem('token');
                        window.location.href = '/logout';
                    });
                },
                fetchAllocatedBooks() {
                    axios.get('/api/allocated_books_user', {
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                    })
                        .then(response => {
                            this.books = response.data;
                        })
                        .catch(error => console.error('Error fetching allocated books:', error));
                },
                Returnbook(bookId) {
                    axios.post('/api/return_book', { book_id: bookId }, {
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                    })
                        .then(response => {
                            alert(response.data.message);
                            this.fetchAllocatedBooks(); // Refresh the list after deallocation
                        })
                        .catch(error => {
                            console.error('Error deallocating the book:', error);
                            alert('Failed to deallocate the book. Please try again.');
                        });
                },
                rateAndFeedbackBook(bookId, rating, feedback) {
                    axios.post('/api/rate_and_feedback_book', {
                        book_id: bookId, rating: rating, feedback: feedback
                    }, {
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        }
                    }).then(response => {
                        alert(response.data.message);
                        this.fetchAllocatedBooks(); // Optionally refresh or update the local state
                    }).catch(error => {
                        console.error('Error submitting feedback:', error);
                        alert('Failed to submit feedback. Please try again.');
                    });
                }
            }
        }).mount('#app8');