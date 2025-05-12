const { createApp } = Vue;
const api = createAuthenticatedApi()
createApp({
    data() {
        return {
            incidents: [],
            activeVehicles: 5,
            map: null,
            markers: [],
            showDetails: false,
            useSatellite: true,
            mapLayer: null,
            showConfirmModal: false,
            selectedIncident: {},
            fetchInterval: null,
            isLoading: false,
            lastUpdated: null
        }
    },

    watch: {
        useSatellite(newValue) {
            if (this.mapLayer) {
                this.map.removeLayer(this.mapLayer);
            }

            if (newValue) {
                // Satellite view
                this.mapLayer = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
                    attribution: '© Google Maps',
                    maxZoom: 20
                }).addTo(this.map);
            } else {
                // Standard map view
                this.mapLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }).addTo(this.map);
            }
        }
    },
    computed: {
        totalIncidents() {
            return this.incidents.length;
        },
        averageSeverity() {
            if (this.incidents.length === 0) return 0;
            const total = this.incidents.reduce((acc, inc) => acc + (inc.severity || 0), 0);
            return total / this.incidents.length;
        }
    },
    methods: {
        toggleDetails() {
            this.showDetails = !this.showDetails;
        },
        getSeverityClass(severity) {
            if (severity === undefined || severity === null) return 'bg-gray-100 text-gray-800';
            if (severity >= 7) return 'bg-red-100 text-red-800';
            if (severity >= 4) return 'bg-yellow-100 text-yellow-800';
            return 'bg-green-100 text-green-800';
        },
        getSeverityColor(severity) {
            if (severity === undefined || severity === null) return '#9CA3AF';
            if (severity >= 7) return '#EF4444';
            if (severity >= 4) return '#F59E0B';
            return '#10B981';
        },
        formatSeverity(severity) {
            return severity !== undefined && severity !== null ? severity.toFixed(1) : 'N/A';
        },
        createWarningIcon(color) {
            return `
                        <svg class="icon" viewBox="0 0 24 24" fill="${color}">
                            <path d="M12 5.99L19.53 19H4.47L12 5.99M12 2L1 21h22L12 2zm1 14h-2v2h2v-2zm0-6h-2v4h2v-4z"/>
                        </svg>
                        <div class="pulse-ring" style="background-color: ${color}"></div>
                    `;
        },
        showAttendModal(incident) {
            this.selectedIncident = incident;
            this.showConfirmModal = true;
        },
        cancelAttend() {
            this.showConfirmModal = false;
            this.selectedIncident = {};
        },
        confirmAttend() {
            // Here you would handle the actual attendance logic
            console.log(`Attending to incident: ${this.selectedIncident.id}`);

            // Update incident status if needed
            const index = this.incidents.findIndex(i => i.id === this.selectedIncident.id);
            if (index !== -1) {
                // For example, you could mark it as attended
                // this.incidents[index].status = 'Attended';
            }

            // Close the confirmation modal
            this.showConfirmModal = false;

            // Close the popup on the map
            this.map.closePopup();

            // Optionally show a success message
            alert(`You are now attending to incident ${this.selectedIncident.vehicleId}`);

            // Reset the selected incident
            this.selectedIncident = {};
        },
        addMarker(incident) {
            // Ensure incident has lat and lng properties
            if (!incident.lat || !incident.lng) {
                console.warn('Incident missing coordinates:', incident);
                return;
            }

            const color = this.getSeverityColor(incident.score);

            // Create custom icon element
            const iconHtml = this.createWarningIcon(color);
            const customIcon = L.divIcon({
                className: 'marker-icon',
                html: iconHtml,
                iconSize: [30, 30]
            });

            // Create marker with custom icon
            const marker = L.marker([incident.lat, incident.lng], {
                icon: customIcon
            });

            // Get the Vue instance reference for use in popup
            const self = this;

            // Create popup content with modern button
            const popupContent = `
                        <div class="p-3">
                            <h3 class="font-bold text-gray-800 mb-2 text-lg">Incident Details</h3>
                            <div class="space-y-1 mb-4">
                                <p class="text-sm"><strong>Vehicle:</strong> ${incident.vehicleId || 'Unknown'}</p>
                                <p class="text-sm"><strong>Time:</strong> ${incident.timestamp || 'Unknown'}</p>
                                <p class="text-sm"><strong>Severity:</strong> ${this.formatSeverity(incident.score)}</p>
                                <p class="text-sm"><strong>Description:</strong> ${incident.description || 'No description'}</p>
                            </div>
                            <div class="text-center">
                                <button id="attend-btn-${incident.id}" class="modern-button w-full bg-gradient-to-r from-blue-500 to-blue-700 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                                    </svg>
                                    Attend Incident
                                </button>
                            </div>
                        </div>
                    `;

            // Add popup to marker
            const popup = L.popup({
                maxWidth: 300,
                className: 'custom-popup'
            }).setContent(popupContent);

            marker.bindPopup(popup);

            // Add event listener to the attend button after popup is opened
            marker.on('popupopen', function () {
                document.getElementById(`attend-btn-${incident.id}`).addEventListener('click', function () {
                    self.showAttendModal(incident);
                });
            });

            // Add marker to map and store in markers array
            marker.addTo(this.map);
            this.markers.push(marker);
        },
        initMap() {
            const center = [-17.8275, 31.0528]; // Default center
            this.map = L.map('map').setView(center, 15);

            // Initialize with satellite view (since useSatellite is true by default)
            this.mapLayer = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
                attribution: '© Google Maps',
                maxZoom: 17
            }).addTo(this.map);

            // Only add markers if we already have incidents (usually not on first load)
            if (this.incidents && this.incidents.length > 0) {
                console.log("Should indicate.....")
                this.incidents.forEach(incident => {
                    this.addMarker(incident);
                });

                if (this.markers.length > 0) {
                    const group = new L.featureGroup(this.markers);
                    this.map.fitBounds(group.getBounds().pad(0.1));
                }
            }
        },
        async fetchIncidentData() {
            try {
                this.isLoading = true;

                let responseData;

                try {
                    // Make API request
                    const response = await api.get('/api/v1/incidents',
                        { headers: { 'Content-Type': 'application/json' } }
                    );
                    responseData = response.data;
                } catch (apiError) {
                    console.warn('API not available, using mock data:', apiError);
                    // Use your existing mock data
                    responseData = [
                        {
                            id: '1',
                            vehicleId: 'VEH-001',
                            timestamp: new Date().toLocaleTimeString(),
                            lat: -17.8275,
                            lng: 31.0528,
                            severity: 8.5,
                            description: 'Vehicle collision detected',
                            location: 'Main Street & 5th Avenue'
                        },
                        // Additional mock data...
                    ];
                }

                // Update incidents data
                if (responseData && Array.isArray(responseData)) {
                    // Process data, same as before
                    this.incidents = responseData.map(incident => ({
                        ...incident,
                        id: incident.id || `temp-${Math.random().toString(36).substring(2, 9)}`,
                        severity: incident.severity !== undefined ? incident.severity : null,
                        vehicleId: incident.vehicleId || 'Unknown',
                        timestamp: incident.timestamp || new Date().toLocaleTimeString(),
                        location: incident.location || 'Unknown location',
                        description: incident.description || 'No description available'
                    }));

                    console.log('Incidents updated:', this.incidents);

                    // Important: Make sure the map is initialized before updating markers
                    if (!this.map) {
                        this.initMap();
                    } else {
                        this.updateMapMarkers();
                    }

                    this.lastUpdated = new Date().toLocaleTimeString();
                }
            } catch (error) {
                console.error('Error fetching incident data:', error);
            } finally {
                this.isLoading = false;
            }
        },
        // Method to update map markers based on new data
        updateMapMarkers() {
            // Clear existing markers
            this.markers.forEach(marker => {
                this.map.removeLayer(marker);
            });
            this.markers = [];

            // Add new markers
            this.incidents.forEach(incident => {
                // Log each incident to debug coordinate issues
                console.log(`Adding marker for incident ${incident.id} at [${incident.lat}, ${incident.lng}]`);
                this.addMarker(incident);
            });

            // Adjust map bounds only if we have markers
            if (this.markers.length > 0) {
                const group = new L.featureGroup(this.markers);
                this.map.fitBounds(group.getBounds().pad(0.1));
            }
        },

        // Method to start the polling interval
        startPolling() {
            // Clear any existing interval first
            this.stopPolling();

            // Initial fetch
            this.fetchIncidentData();

            // Set up the interval (5000ms = 5 seconds)
            this.fetchInterval = setInterval(() => {
                this.fetchIncidentData();
            }, 10000);
        },

        // Method to stop the polling interval
        stopPolling() {
            if (this.fetchInterval) {
                clearInterval(this.fetchInterval);
                this.fetchInterval = null;
            }
        }
    },
    // Add created lifecycle hook to start polling when component is created
    created() {
        // Start polling when component is created
        this.startPolling();
    },

    // Add beforeUnmount lifecycle hook to clean up
    beforeUnmount() {
        // Stop polling when component is unmounted to prevent memory leaks
        this.stopPolling();
    },
    mounted() {

        this.$nextTick(() => {
            // Only initialize map if it hasn't been initialized yet
            if (!this.map) {
                this.initMap();
            }

            // Start polling for data
            this.startPolling();
        });


    }
}).mount('#app')