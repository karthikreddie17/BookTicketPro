const { createApp } = Vue;
    createApp({
        data() {
            return {
                sectionId: null,
                newSection: {
                    name: '',
                    description: '',
                }
            };
        },
        mounted() {
            this.setupLogoutListener();
            this.sectionId = new URLSearchParams(window.location.search).get('sectionId');
            if (this.sectionId) {
                this.fetchSectionDetails(this.sectionId);
            }
        },
        methods: {
             setupLogoutListener() {
                document.getElementById('logoutButton').addEventListener('click', () => {
                    localStorage.removeItem('token');
                    window.location.href = '/logout';
                });
            },
            fetchSectionDetails(sectionId) {
                const token = localStorage.getItem('token');
                const headers = { 'Authorization': `Bearer ${token}` };
                axios.get(`/api/sections/${sectionId}`, { headers })
                    .then(response => {
                        if (response.data) {
                            this.newSection.name = response.data.name;
                            this.newSection.description = response.data.description;
                          
                        } else {
                            console.error('No data returned for section:', sectionId);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching section details:', error);
                    });
            },
            addOrUpdateSection() {
                const token = localStorage.getItem('token');
                const headers = { 'Authorization': `Bearer ${token}` };
                const url = this.sectionId ? `/api/sections/${this.sectionId}` : '/api/sections';
                const method = this.sectionId ? 'put' : 'post';

                axios[method](url, this.newSection, { headers })
                    .then(response => {
                        alert(`Section ${this.sectionId ? 'updated' : 'added'} successfully`);
                        // Redirect or clear form based on your needs
                        window.location.href = `/librarian_dashboard`;
                    })
                    .catch(error => {
                        console.error(`Error ${this.sectionId ? 'updating' : 'adding'} section:`, error);
                        alert(`Error ${this.sectionId ? 'updating' : 'adding'} section`);
                    });
            }
        }
    }).mount('#app2');