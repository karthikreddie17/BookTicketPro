// document.getElementById('logoutButton').addEventListener('click', function () {
            //     localStorage.removeItem('token');
            //     window.location.href = '/logout';
            // });
            const app1 = Vue.createApp({
                data() {
                    return {
                        sections: [],
                        searchTerm: '',
                        isProcessing: false,
                        taskId: null
                    };
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
                },
                methods: {
                    fetchSections() {
                        const token = localStorage.getItem('token');
                        const headers = { 'Authorization': `Bearer ${token}` };
                        axios.get('/api/sections', { headers })
                            .then(response => {
                                this.sections = response.data.sections;
                                this.sections.forEach(section => {
                                    this.fetchBooksForSection(section);
                                });
                            })
                            .catch(error => {
                                console.error('Error fetching sections:', error);
                            });
                    },
                    fetchBooksForSection(section) {
                        const token = localStorage.getItem('token');
                        const headers = { 'Authorization': `Bearer ${token}` };
                        axios.get(`/api/sections/${section.id}/books`, { headers })
                            .then(response => {
                                section.books = response.data.books;
                            })
                            .catch(error => {
                                console.error(`Error fetching books for section ${section.id}:`, error);
                                section.books = [];
                            });
                    },
                    todelSection(sectionId) {
                        const token = localStorage.getItem('token');
                        const headers = {
                            'Authorization': `Bearer ${token}`
                        };

                        axios.delete(`/api/sections/${sectionId}`, { headers })
                            .then(response => {
                                console.log('Section deleted successfully:', response.data);
                                this.fetchSections();
                            })
                            .catch(error => {
                                console.error('Error deleting section:', error);
                                alert('Error deleting section');
                            });
                    },
                    toaddBook(sectionId) {
                        window.location.href = `/add_book?sectionId=${sectionId}`;
                    },
                    navigateToSection(sectionId) {
                        window.location.href = `/add_section?sectionId=${sectionId}`;
                    },
                    navigateToBook(sectionId, bookId) {
                        window.location.href = `/add_book?sectionId=${sectionId}&bookId=${bookId}`;
                    },
                    todelBook(sectionId, bookId) {
                        const token = localStorage.getItem('token');
                        const headers = {
                            'Authorization': `Bearer ${token}`,
                        };
                        axios.delete(`/api/sections/${sectionId}/books/${bookId}`, { headers })
                            .then(response => {
                                this.fetchSections();
                            })
                            .catch(error => {
                                alert('Error deleting book');
                            });
                    },
                    setupLogoutListener() {
                        document.getElementById('logoutButton').addEventListener('click', () => {
                            localStorage.removeItem('token');
                            window.location.href = '/logout';
                        });
                    },

                    async triggerExport() {
                        this.isProcessing = true;
                        try {
                            const token = localStorage.getItem('token');
                            const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

                            const response = await axios.post('/trigger-csv-export', { email: 'librarian@mkr.com' }, { headers });
                            this.taskId = response.data.Task_ID;
                            this.pollForCompletion();
                        } catch (error) {
                            console.error("Error triggering export:", error);
                            this.isProcessing = false;
                        }
                    },
                    pollForCompletion() {
                        const token = localStorage.getItem('token');
                        const headers = { 'Authorization': `Bearer ${token}` };

                        const interval = setInterval(async () => {
                            try {
                                const response = await axios.get(`/status/${this.taskId}`, { headers });
                                const data = response.data;

                                if (data.Task_State === "SUCCESS") {
                                    this.isProcessing = false;
                                    clearInterval(interval);
                                    window.location.href = '/download-csv';  // Redirect to download the CSV
                                }
                            } catch (error) {
                                console.error("Error polling for completion:", error);
                            }
                        }, 3000);  // Poll every 3 seconds
                    }
                }


            }).mount('#app1');