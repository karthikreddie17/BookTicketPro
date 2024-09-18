// document.getElementById('logoutButton').addEventListener('click', function () {
        //     localStorage.removeItem('token');
        //     window.location.href = '/logout';
        // });
        const app5 = Vue.createApp({
            data() {
                return {
                    sections: [],
                    // userId: '',
                    liveTime: '',
                    searchTerm: ''
                };
            },
            created() {
                this.updateTime();  // Initialize the time
                setInterval(this.updateTime, 1000);  // Update the time every second
            },
            computed: {
                filteredSections() {
                    if (!this.searchTerm) return this.sections;

                    return this.sections.filter(section => {
                        const booksMatch = section.books.some(book =>
                            book.title.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
                            book.authors.toLowerCase().includes(this.searchTerm.toLowerCase())
                        );
                        return section.name.toLowerCase().includes(this.searchTerm.toLowerCase()) || booksMatch;
                    });
                }
            },
            mounted() {
                this.fetchSections();
                this.setupLogoutListener();
                this.initializeBookStatus();

            },
            methods: {
                updateTime() {
                    const now = new Date();
                    this.liveTime = now.toLocaleTimeString();  // Formats the time according to the locale
                },
                initializeBookStatus() {
                    const token = localStorage.getItem('token');
                    axios.post('/api/initialize_book_status', {}, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    }).then(response => {
                        console.log("Book statuses initialized:", response.data.message);
                        this.fetchSections();
                    }).catch(error => {
                        console.error('Error initializing book statuses:', error);
                    });
                },
                fetchSections() {
                    const token = localStorage.getItem('token');
                    const headers = { 'Authorization': `Bearer ${token}` };
                    axios.get('/api/sections', { headers })
                        .then(response => {
                            console.log("Sections fetched:", response.data.sections);
                            this.sections = response.data.sections;
                            this.sections.forEach(section => {
                                this.fetchBooksForSection(section);
                            });
                        })
                        .catch(error => {
                            console.error('Error fetching sections:', error);
                            alert(error.response.data.message);
                        });
                },


                fetchBooksForSection(section) {
                    const token = localStorage.getItem('token');
                    const headers = { 'Authorization': `Bearer ${token}` };
                    axios.get(`/api/sections/${section.id}/books`, { headers })
                        .then(response => {
                            console.log(`Books fetched for section ${section.id}:`, response.data.books);
                            this.sections = this.sections.map(s => {
                                if (s.id === section.id) {
                                    return { ...s, books: response.data.books };
                                }
                                return s;
                            });
                            console.log("Updated sections with books:", this.sections);

                        })
                        .catch(error => {
                            console.error(`Error fetching books for section ${section.id}:`, error);
                            console.log(error.response);
                            section.books = []; // Handle cases where no books are found
                        });
                },
                requestBook(book) {
                    console.log("Requesting book with data:", book);
                    if (!book.id) {
                        console.error("Book ID is undefined, cannot proceed with the request.");
                        return;
                    }
                    axios.post(`/api/books/${book.id}/request`, {}, {
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                    }).then(response => {
                        alert('Request sent successfully.');

                        book.status = response.data.status;

                    }).catch(error => {
                        console.error('Error requesting book:', error);
                        alert(error.response.data.message);
                    });
                },
                setupLogoutListener() {
                    document.getElementById('logoutButton').addEventListener('click', () => {
                        localStorage.removeItem('token');
                        window.location.href = '/logout';
                    });
                },
            }



        }).mount('#app5');