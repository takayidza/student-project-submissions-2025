const { createApp, ref, computed, onMounted } = Vue
const api = createAuthenticatedApi()

createApp({
    setup() {
        // Basic UI state
        const sidebarCollapsed = ref(false)
        const activeTab = ref('dashboard')
        const pageTitle = ref('Dashboard')
        const filteredUsers = ref([])

        // IoT Devices Data
        const devices = ref([])

        // Vehicles Data
        const vehicles = ref([])

        //Notifications
        const notifications = ref([])

        // Users Data
        const users = ref([])
        const unfilteredUsers = ref([])
        const userSearchQuery = ref('')
        const showUserEditModal = ref(false)
        const editingUser = ref(null)
        const newUser = ref({
            full_name: '',
            phone_number: '',
            email: '',
            city: '',
            home_address: ''
        })

        // Form states
        const newDevice = ref({
            device_id: '',
            vehicle_id: '',
            is_active: true,
        })

        const newVehicle = ref({
            vehicle_name: '',
            vehicle_type: '',
            reg: '',
            model: '',
            year: new Date().getFullYear(),
            colour: '',
            user_id: '' // Add user_id field
        })

        // UI states
        const vehicleSearchQuery = ref('')
        const vehicleFilter = ref('all')
        const showVehicleEditModal = ref(false)
        const editingVehicle = ref(null)
        const showAssignIotModal = ref(false)
        const assigningVehicle = ref(null)
        const selectedIotDevice = ref('')
        const iotInstallationDate = ref(new Date().toISOString().split('T')[0])
        const deviceSearchQuery = ref('')
        const deviceFilter = ref('all')
        const showEditModal = ref(false)
        const editingDevice = ref(null)
        const notificationFilter = ref('all')
        const notificationSearchQuery = ref('')
        const showNotificationModal = ref(false)
        const selectedNotification = ref(null)

        // API Integration Functions
        const apiService = {
            async getUsers() {
                try {
                    const response = await api.get('/api/v1/users')
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async getUser(userId) {
                try {
                    const response = await api.get(`/api/v1/users/${userId}`)
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async addUser(userData) {
                try {
                    const response = await api.post('/api/v1/users', {
                        name: userData.name,
                        phone: userData.phone,
                        email: userData.email,
                        city: userData.city,
                        address: userData.address
                    })
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async updateUser(userId, userData) {
                try {
                    const response = await api.put(`/api/v1/users/${userId}`, userData)
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async deleteUser(userId) {
                try {
                    const response = await api.delete(`/api/v1/users/${userId}`)
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async addDevice(deviceData) {
                try {
                    const response = await api.post('/api/v1/devices', deviceData)
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async updateDevice(deviceId, deviceData) {
                try {
                    const response = await api.put(`/api/v1/devices/${deviceId}`, deviceData)
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async getDevices() {
                try {
                    const response = await api.get('/api/v1/devices')
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async addVehicle(vehicleData) {
                try {
                    const response = await api.post('/api/v1/vehicles', vehicleData)
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async updateVehicle(vehicleId, vehicleData) {
                try {
                    const response = await api.put(`/api/v1/vehicles/${vehicleId}`, vehicleData)
                    return response.data
                } catch (error) {
                    throw error
                }
            },

            async getVehicles() {
                try {
                    const response = await api.get('/api/v1/vehicles')
                    return response.data
                } catch (error) {
                    throw error
                }
            }
        }

        // Computed Properties
        const activeDevices = computed(() => {
            return devices.value.filter(device => device.is_active).length
        })

        const unreadNotifications = computed(() => {
            return notifications.value.filter(notif => notif.status === 'unread').length
        })

        const filteredNotifications = computed(() => {
            let filtered = [...notifications.value]

            // Apply search
            if (notificationSearchQuery.value) {
                const query = notificationSearchQuery.value.toLowerCase()
                filtered = filtered.filter(notif =>
                    notif.message.toLowerCase().includes(query) ||
                    getVehicleName(notif.vehicle_id).toLowerCase().includes(query)
                )
            }

            // Apply filters
            if (notificationFilter.value !== 'all') {
                switch (notificationFilter.value) {
                    case 'unread':
                        filtered = filtered.filter(notif => notif.status === 'unread')
                        break
                    case 'high':
                        filtered = filtered.filter(notif => notif.severity === 'high')
                        break
                    case 'medium':
                        filtered = filtered.filter(notif => notif.severity === 'medium')
                        break
                    case 'low':
                        filtered = filtered.filter(notif => notif.severity === 'low')
                        break
                }
            }

            // Sort by timestamp (newest first)
            return filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        })

        const activeDevicesPercentage = computed(() => {
            return devices.value.length > 0
                ? Math.round((activeDevices.value / devices.value.length) * 100)
                : 0
        })

        const maintenanceDueCount = computed(() => {
            const thirtyDaysAgo = new Date()
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

            return devices.value.filter(device => {
                if (!device.last_maintenance) return true
                return new Date(device.last_maintenance) < thirtyDaysAgo
            }).length
        })

        const filteredDevices = computed(() => {
            let filtered = [...devices.value]

            if (deviceSearchQuery.value) {
                const query = deviceSearchQuery.value.toLowerCase()
                filtered = filtered.filter(device =>
                    device.device_serial.toLowerCase().includes(query) ||
                    getVehicleName(device.vehicle_id).toLowerCase().includes(query)
                )
            }

            if (deviceFilter.value !== 'all') {
                const thirtyDaysAgo = new Date()
                thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

                switch (deviceFilter.value) {
                    case 'active':
                        filtered = filtered.filter(device => device.is_active)
                        break
                    case 'inactive':
                        filtered = filtered.filter(device => !device.is_active)
                        break
                    case 'maintenance':
                        filtered = filtered.filter(device => {
                            if (!device.last_maintenance) return true
                            return new Date(device.last_maintenance) < thirtyDaysAgo
                        })
                        break
                }
            }

            return filtered
        })

        const vehiclesWithIot = computed(() => {
            if (!devices.value || !vehicles.value) return 0
            const connectedVehicleIds = new Set(devices.value.map(device => device.vehicle_id))
            return vehicles.value.filter(vehicle => connectedVehicleIds.has(vehicle.vehicle_id)).length
        })

        const iotConnectionPercentage = computed(() => {
            if (!vehicles.value || !vehiclesWithIot.value) return 0
            return vehicles.value.length > 0
                ? Math.round((vehiclesWithIot.value / vehicles.value.length) * 100)
                : 0
        })

        const vehicleMaintenanceDue = computed(() => {
            // Placeholder - implement actual maintenance check logic
            return Math.floor(vehicles.value.length * 0.2)
        })

        const filteredVehicles = computed(() => {
            if (!vehicles.value) return [] // Return empty array if vehicles is undefined
            
            let filtered = [...vehicles.value]
        
            // Apply search query
            if (vehicleSearchQuery.value) {
                const query = vehicleSearchQuery.value.toLowerCase()
                filtered = filtered.filter(vehicle => {
                    if (!vehicle) return false // Skip undefined vehicles
                    return vehicle.vehicle_name?.toLowerCase().includes(query) ||
                           vehicle.reg?.toLowerCase().includes(query) ||
                           vehicle.model?.toLowerCase().includes(query)
                })
            }
        
            // Apply filters
            if (vehicleFilter.value !== 'all') {
                const connectedVehicleIds = new Set(devices.value.map(device => device.vehicle_id))
        
                filtered = filtered.filter(vehicle => {
                    if (!vehicle) return false // Skip undefined vehicles
                    
                    switch (vehicleFilter.value) {
                        case 'active':
                            return vehicle.is_active === true
                        case 'inactive':
                            return vehicle.is_active === false
                        case 'connected':
                            return connectedVehicleIds.has(vehicle.vehicle_id)
                        case 'not_connected':
                            return !connectedVehicleIds.has(vehicle.vehicle_id)
                        default:
                            return true
                    }
                })
            }
        
            return filtered
        })

        const unassignedVehicles = computed(() => {
            if (!users.value || !vehicles.value) return vehicles.value || []
            const assignedVehicleIds = new Set(users.value.filter(user => user?.vehicleId).map(user => user.vehicleId))
            return vehicles.value.filter(vehicle => !assignedVehicleIds.has(vehicle.vehicle_id))
        })

        const filteredUserz = computed(() => {
            if (!users.value || users.value.length === 0) return []

            const allUsers = [...users.value]
            console.log('All Users:', allUsers) 
            if (!userSearchQuery.value) return allUsers

            const query = userSearchQuery.value.toLowerCase()
            return allUsers.filter(user => {
                if (!user) return false
                return (user.full_name && user.full_name.toLowerCase().includes(query)) ||
                       (user.email && user.email.toLowerCase().includes(query)) ||
                       (user.phone_number && user.phone_number.includes(query))
            })

        })

        // Methods
        const toggleSidebar = () => {
            sidebarCollapsed.value = !sidebarCollapsed.value
        }

        const setActiveTab = (tab) => {
            activeTab.value = tab
            updatePageTitle()
        }

        const updatePageTitle = () => {
            const titles = {
                'dashboard': 'Dashboard',
                'iot': 'IoT Devices',
                'vehicles': 'Vehicles',
                'alerts': 'Alerts',
                'users': 'Users Management'
            }
            pageTitle.value = titles[activeTab.value] || 'Dashboard'
        }

        const formatDate = (dateString) => {
            if (!dateString) return 'N/A'
            return new Date(dateString).toLocaleDateString()
        }

        const getVehicleName = (vehicleId) => {
            const vehicle = vehicles.value.find(v => v.vehicle_id === vehicleId)
            return vehicle ? vehicle.vehicle_name : 'Unknown Vehicle'
        }

        const hasIotDevice = (vehicleId) => {
            if (!devices.value) return false
            return devices.value.some(device => device.vehicle_id === vehicleId)
        }

        const getVehicleOwner = (userId) => {
            if (!userId || !users.value) return 'No owner assigned'
            const owner = users.value.find(u => u.user_id === userId)
            return owner ? owner.full_name : 'No owner assigned'
        }

        const addNewDevice = async () => {
            try {
                const response = await apiService.addDevice(newDevice.value)
                if (response.status) {
                    const newId = Math.max(...devices.value.map(d => d.association_id), 0) + 1
                    devices.value.push({
                        association_id: newId,
                        device_serial: newDevice.value.device_id,
                        vehicle_id: newDevice.value.vehicle_id,
                        is_active: newDevice.value.is_active
                    })
                    newDevice.value = {
                        device_id: '',
                        vehicle_id: '',
                        is_active: true
                    }
                    alert('Device added successfully')
                }
            } catch (error) {
                console.error('Error adding device:', error)
                alert('Error adding device. Please try again.')
            }
        }

        const updateDevice = async () => {
            if (!editingDevice.value?.device_id) return

            try {
                const deviceData = {
                    device_id: editingDevice.value.device_serial,
                    vehicle_id: editingDevice.value.vehicle_id,
                    is_active: editingDevice.value.is_active,
                    installation_date: editingDevice.value.installation_date,
                    last_maintenance: editingDevice.value.last_maintenance
                }

                const response = await apiService.updateDevice(editingDevice.value.device_id, deviceData)
                
                if (response.status) {
                    await fetchDevices() // Refresh devices list
                    showEditModal.value = false
                    alert('Device updated successfully')
                }
            } catch (error) {
                console.error('Error updating device:', error)
                alert('Error updating device. Please try again.')
            }
        }

        const addNewVehicle = async () => {
            try {
                // Add console log to debug
                console.log('Submitting vehicle data:', newVehicle.value)
                const response = await apiService.addVehicle(newVehicle.value)
                if (response.status) {
                    const newId = Math.max(...vehicles.value.map(v => v.vehicle_id), 0) + 1
                    vehicles.value.push({
                        vehicle_id: newId,
                        ...newVehicle.value,
                        is_active: true
                    })
                    newVehicle.value = {
                        reg: '',
                        make: '',
                        model: '',
                        year: new Date().getFullYear(),
                        colour: '',
                        user_id: '' // Reset user_id field
                    }
                    alert('Vehicle added successfully')
                }
            } catch (error) {
                console.error('Error adding vehicle:', error)
                alert('Error adding vehicle. Please try again.')
            }
        }

        const editVehicle = (vehicle) => {
            if (!vehicle) {
                console.error('No vehicle provided to editVehicle function');
                return;
            }
            // Create a copy of the vehicle data for editing with proper field names
            editingVehicle.value = {
                vehicle_id: vehicle.vehicle_id,
                registration_number: vehicle.registration_number,
                make: vehicle.make,
                model: vehicle.model,
                year: vehicle.year,
                color: vehicle.color,
                user_id: vehicle.user_id,
                is_active: vehicle.is_active
            };
            showVehicleEditModal.value = true;
        }

        const updateVehicle = async () => {
            if (!editingVehicle.value?.vehicle_id) return

            try {
                // Match backend field names
                const vehicleData = {
                    registration_number: editingVehicle.value.registration_number,
                    make: editingVehicle.value.make,
                    model: editingVehicle.value.model,
                    year: editingVehicle.value.year,
                    color: editingVehicle.value.color,
                    user_id: editingVehicle.value.user_id
                }

                const response = await apiService.updateVehicle(
                    editingVehicle.value.vehicle_id,
                    vehicleData
                )

                if (response.status) {
                    // Update local vehicle data
                    const index = vehicles.value.findIndex(v => v.vehicle_id === editingVehicle.value.vehicle_id)
                    if (index !== -1) {
                        vehicles.value[index] = { ...vehicles.value[index], ...vehicleData }
                    }
                    showVehicleEditModal.value = false
                    alert('Vehicle updated successfully')
                    await fetchVehicles() // Refresh vehicle list
                }
            } catch (error) {
                console.error('Error updating vehicle:', error)
                alert('Error updating vehicle. Please try again.')
            }
        }

        const markAsRead = (notification) => {
            const index = notifications.value.findIndex(n => n.id === notification.id)
            if (index !== -1) {
                notifications.value[index].status = 'read'
            }
        }

        const markAllAsRead = () => {
            notifications.value = notifications.value.map(notif => ({
                ...notif,
                status: 'read'
            }))
        }

        const viewNotificationDetails = (notification) => {
            selectedNotification.value = notification
            showNotificationModal.value = true
            markAsRead(notification)
        }

        const deleteNotification = (notification) => {
            const index = notifications.value.findIndex(n => n.id === notification.id)
            if (index !== -1) {
                notifications.value.splice(index, 1)
            }
        }

        const toggleVehicleStatus = (vehicle) => {
            if (!vehicle || typeof vehicle.vehicle_id === 'undefined') {
                console.error('Invalid vehicle object:', vehicle)
                return
            }
        
            const index = vehicles.value.findIndex(v => v.vehicle_id === vehicle.vehicle_id)
            if (index !== -1) {
                vehicles.value[index].is_active = !vehicles.value[index].is_active
                alert(`Vehicle ${vehicles.value[index].is_active ? 'activated' : 'deactivated'} successfully`)
            }
        }
        
        const toggleDeviceStatus = (device) => {
            if (!device || typeof device.association_id === 'undefined') {
                console.error('Invalid device object:', device)
                return
            }
        
            const index = devices.value.findIndex(d => d.association_id === device.association_id)
            if (index !== -1) {
                devices.value[index].is_active = !devices.value[index].is_active
                alert(`Device ${devices.value[index].is_active ? 'activated' : 'deactivated'} successfully`)
            }
        }

        const editDevice = (device) => {
            if (!device) {
                console.error('No device provided to editDevice function');
                return;
            }
            editingDevice.value = {
                device_id: device.device_id,
                device_serial: device.device_serial,
                vehicle_id: device.vehicle_id,
                installation_date: device.installation_date,
                last_maintenance: device.last_maintenance,
                is_active: device.is_active
            }
            showEditModal.value = true;
        }

        const addNewUser = async () => {
            try {
                const response = await apiService.addUser({
                    name: newUser.value.name,
                    phone: newUser.value.phone,
                    email: newUser.value.email,
                    city: newUser.value.city,
                    address: newUser.value.address
                })

                if (response.status) {
                    await fetchUsers() // Refresh user list
                    // Reset form
                    newUser.value = {
                        name: '',
                        phone: '',
                        email: '',
                        city: '',
                        address: ''
                    }
                    alert('User added successfully')
                }
            } catch (error) {
                console.error('Error adding user:', error)
                alert('Error adding user. Please try again.')
            }
        }

        const getUserVehicles = (user) => {
            if (!user || !vehicles.value) return []
            return vehicles.value.filter(vehicle => vehicle.vehicle_id === user.vehicleId)
        }

        const editUser = (user) => {
            editingUser.value = { ...user }
            showUserEditModal.value = true
        }

        const updateUser = async () => {
            if (!editingUser.value?.user_id){
                console.log('No user provided to updateUser function')
                return
            }

            try {
                const userData = {
                    full_name: editingUser.value.full_name,
                    email: editingUser.value.email,
                    phone_number: editingUser.value.phone_number,
                    city: editingUser.value.city,
                    home_address: editingUser.value.home_address
                }

                const response = await apiService.updateUser(editingUser.value.user_id, userData)
                if (response.error) {
                    throw new Error(response.error)
                }
                await fetchUsers() // Refresh user list
                showUserEditModal.value = false
                alert('User updated successfully')
            } catch (error) {
                console.error('Error updating user:', error)
                alert('Error updating user. Please try again.')
            }
        }

        const deleteUser = async (user) => {
            if (!confirm('Are you sure you want to delete this user?')) return

            try {
                const response = await apiService.deleteUser(user.id)
                if (response.status) {
                    const index = users.value.findIndex(u => u.id === user.id)
                    if (index !== -1) {
                        users.value.splice(index, 1)
                    }
                    alert('User deleted successfully')
                }
            } catch (error) {
                console.error('Error deleting user:', error)
                alert('Error deleting user. Please try again.')
            }
        }

        // Fetch users when component mounts
        const fetchUsers = async () => {
            try {
                const response = await apiService.getUsers()
                console.log('Users fetched:', response)
                users.value = response
            } catch (error) {
                console.error('Error fetching users:', error)
                alert('Error loading users. Please refresh the page.')
            }
        }

        // Fetch vehicles when component mounts
        const fetchVehicles = async () => {
            try {
                const response = await apiService.getVehicles()
                console.log('Vehicles fetched:', response)
                vehicles.value = response
            } catch (error) {
                console.error('Error fetching vehicles:', error)
                alert('Error loading vehicles. Please refresh the page.')
            }
        }

        // Fetch devices when component mounts
        const fetchDevices = async () => {
            try {
                const response = await apiService.getDevices()
                console.log('Devices fetched:', response) 
                devices.value = response
            } catch (error) {
                console.error('Error fetching devices:', error)
                alert('Error loading devices. Please refresh the page.')
            }
        }

        // Call fetchUsers, fetchVehicles, and fetchDevices immediately on mount
        onMounted(() => {
            fetchUsers()
            fetchVehicles()
            fetchDevices()
        })

        return {
            // State
            sidebarCollapsed,
            activeTab,
            pageTitle,
            devices,
            vehicles,
            newDevice,
            newVehicle,
            vehicleSearchQuery,
            vehicleFilter,
            showVehicleEditModal,
            editingVehicle,
            showAssignIotModal,
            assigningVehicle,
            selectedIotDevice,
            iotInstallationDate,
            deviceSearchQuery,
            deviceFilter,
            showEditModal,
            editingDevice,
            notifications,
            notificationFilter,
            notificationSearchQuery,
            showNotificationModal,
            selectedNotification,
            unreadNotifications,
            filteredNotifications,
            users,
            showUserEditModal,
            editingUser,
            userSearchQuery,
            newUser,

            // Computed
            activeDevices,
            activeDevicesPercentage,
            maintenanceDueCount,
            filteredDevices,
            vehiclesWithIot,
            iotConnectionPercentage,
            vehicleMaintenanceDue,
            filteredVehicles,
            unassignedVehicles,
            filteredUserz,

            // Methods
            toggleSidebar,
            setActiveTab,
            updatePageTitle,
            formatDate,
            getVehicleName,
            hasIotDevice,
            getVehicleOwner,
            addNewDevice,
            updateDevice,
            addNewVehicle,
            updateVehicle,
            markAsRead,
            markAllAsRead,
            viewNotificationDetails,
            deleteNotification,
            toggleVehicleStatus,
            toggleDeviceStatus,
            editVehicle,
            editDevice,
            addNewUser,
            getUserVehicles,
            editUser,
            updateUser,
            deleteUser,
            fetchUsers,
            fetchVehicles,
            fetchDevices
        }
    }
}).mount('#app')