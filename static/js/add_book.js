const app3 = Vue.createApp({
        data() {
            return {
                sectionId: null,
                bookId: null,
                newBook: {
                    title: '',
                    authors: '',
                    content: '',
                    rating: null
                }
            };
        },
        methods: {
            setupLogoutListener() {
                document.getElementById('logoutButton').addEventListener('click', () => {
                    localStorage.removeItem('token');
                    window.location.href = '/logout';
                });
            },
            addOrUpdateBook() {
                const token = localStorage.getItem('token');
                const headers = { 'Authorization': `Bearer ${token}` };
                const url = this.bookId ? `/api/sections/${this.sectionId}/books/${this.bookId}` : `/api/sections/${this.sectionId}/books`;
                const method = this.bookId ? 'put' : 'post';

                axios({
                    method: method,
                    url: url,
                    data: this.newBook,
                    headers: headers
                }).then(response => {
                    alert(`Book ${this.bookId ? 'updated' : 'added'} successfully`);
                    window.location.href='/librarian_dashboard'
                    if (!this.bookId) {
                        this.newBook = { title: '', authors: '', content: '', rating: '' }; // Clear the form only if adding a new book
                    }
                }).catch(error => {
                    console.error('Error adding/updating book:', error.response.data);
                    alert('Error adding/updating book: ' + (error.response.data.message || 'Unknown error'));
                });
            },
            fetchBookDetails(sectionId, bookId) {
                const token = localStorage.getItem('token');
                const headers = { 'Authorization': `Bearer ${token}` };
                axios.get(`/api/sections/${sectionId}/books/${bookId}`, { headers })
                    .then(response => {
                        if (response.data) {
                            this.newBook = {
                                title: response.data.title,
                                authors: response.data.authors,
                                content: response.data.content,
                                rating: response.data.rating
                            };
                        }
                    }).catch(error => {
                        console.error('Error fetching book details:', error);
                    });
            }
        },
        mounted() {
            this.setupLogoutListener();
            const urlParams = new URLSearchParams(window.location.search);
            this.sectionId = urlParams.get('sectionId');
            this.bookId = urlParams.get('bookId');
            if (this.bookId) {
                this.fetchBookDetails(this.sectionId, this.bookId);
            }
        }
    }).mount('#app3');  