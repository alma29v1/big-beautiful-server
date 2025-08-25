import Foundation
import Combine

class DataManager: ObservableObject {
    @Published var houses: [House] = []
    @Published var incidents: [Incident] = []
    @Published var salespeople: [SalesPerson] = []
    @Published var routes: [Route] = []
    @Published var visits: [Visit] = []

    // Big Beautiful Program Integration
    @Published var bigBeautifulAPIClient = BigBeautifulAPIClient()
    @Published var contacts: [Contact] = []
    @Published var analytics: AnalyticsResponse?
    @Published var isBigBeautifulConnected = false

    // Email Campaign Data
    @Published var emailCampaigns: [EmailCampaign] = []
    @Published var emailStats: EmailStats?
    @Published var selectedCampaignRecipients: [EmailRecipient] = []
    @Published var lastSyncTimestamp: Date?
    @Published var regionAssignments: [String: UUID] = [:] // city -> salespersonId

    private let userDefaults = UserDefaults.standard

    init() {
        loadSampleData()
        loadRegionAssignments()

        // Connect to Big Beautiful Program on startup
        Task {
            await connectToBigBeautifulProgram()
        }
    }

    // MARK: - Sample Data

    private func loadSampleData() {
        // Sample salespeople
        salespeople = [
            SalesPerson(name: "Mike Sales", email: "mike@company.com", phone: "910-555-0201"),
            SalesPerson(name: "Sarah Closer", email: "sarah@company.com", phone: "910-555-0202"),
            SalesPerson(name: "Tom Door", email: "tom@company.com", phone: "910-555-0203")
        ]

        // Load minimal sample data - most data will come from Big Beautiful Program
        loadMinimalSampleData()
    }

    private func loadMinimalSampleData() {
        // Only load essential sample data for demonstration
        // Real data will come from Big Beautiful Program

        // Sample houses (will be replaced by contacts from Big Beautiful Program)
        houses = [
            House(address: "123 Main St", city: "Wilmington", state: "NC", zipCode: "28401",
                  latitude: 34.2257, longitude: -77.9447, soldDate: "2024-01-15", price: 250000,
                  contactName: "John Smith", contactEmail: "john@email.com", contactPhone: "910-555-0101",
                  fiberAvailable: true, adtDetected: false),

            House(address: "456 Oak Ave", city: "Leland", state: "NC", zipCode: "28451",
                  latitude: 34.2563, longitude: -78.0447, soldDate: "2024-01-16", price: 275000,
                  contactName: "Jane Doe", contactEmail: "jane@email.com", contactPhone: "910-555-0102",
                  fiberAvailable: false, adtDetected: true),

            House(address: "789 Pine Rd", city: "Southport", state: "NC", zipCode: "28461",
                  latitude: 33.9207, longitude: -78.0189, soldDate: "2024-01-17", price: 300000,
                  contactName: "Bob Johnson", contactEmail: "bob@email.com", contactPhone: "910-555-0103",
                  fiberAvailable: true, adtDetected: false)
        ]

        // Sample incidents
        incidents = [
            Incident(address: "123 Main St", incidentType: .fire, description: "House fire in neighborhood",
                     latitude: 34.2257, longitude: -77.9447, assignedSalespersonId: salespeople[0].id),

            Incident(address: "456 Oak Ave", incidentType: .breakIn, description: "Recent break-in reported",
                     latitude: 34.2563, longitude: -78.0447, assignedSalespersonId: salespeople[1].id),

            Incident(address: "789 Pine Rd", incidentType: .flood, description: "Flood damage reported",
                     latitude: 33.9207, longitude: -78.0189, assignedSalespersonId: salespeople[2].id)
        ]

        // Sample routes
        let wilmingtonHouses = houses.filter { $0.city == "Wilmington" }.map { $0.id }
        let lelandHouses = houses.filter { $0.city == "Leland" }.map { $0.id }

        routes = [
            Route(name: "Wilmington Route 1", salespersonId: salespeople[0].id, houseIds: Array(wilmingtonHouses.prefix(2))),
            Route(name: "Leland Route 1", salespersonId: salespeople[1].id, houseIds: Array(lelandHouses.prefix(2)))
        ]

        // Sample visits
        visits = [
            Visit(houseId: houses[0].id, salespersonId: salespeople[0].id, status: .contacted, notes: "Spoke with homeowner about security options"),
            Visit(houseId: houses[1].id, salespersonId: salespeople[1].id, status: .interested, notes: "Interested in ADT system", followUpDate: Date().addingTimeInterval(7*24*60*60))
        ]
    }

    // MARK: - House Operations

    func updateHouse(_ house: House) {
        if let index = houses.firstIndex(where: { $0.id == house.id }) {
            houses[index] = house
            saveData()
        }
    }

    func addHouse(_ house: House) {
        houses.append(house)
        saveData()
    }

    func deleteHouse(_ house: House) {
        houses.removeAll { $0.id == house.id }
        saveData()
    }

    // MARK: - Incident Operations

    func updateIncident(_ incident: Incident) {
        if let index = incidents.firstIndex(where: { $0.id == incident.id }) {
            incidents[index] = incident
            saveData()
        }
    }

    func addIncident(_ incident: Incident) {
        incidents.append(incident)
        saveData()
    }

    func deleteIncident(_ incident: Incident) {
        incidents.removeAll { $0.id == incident.id }
        saveData()
    }

    // MARK: - Route Operations

    func updateRoute(_ route: Route) {
        if let index = routes.firstIndex(where: { $0.id == route.id }) {
            routes[index] = route
            saveData()
        }
    }

    func addRoute(_ route: Route) {
        routes.append(route)
        saveData()
    }

    func deleteRoute(_ route: Route) {
        routes.removeAll { $0.id == route.id }
        saveData()
    }

    // MARK: - Visit Operations

    func updateVisit(_ visit: Visit) {
        if let index = visits.firstIndex(where: { $0.id == visit.id }) {
            visits[index] = visit
            saveData()
        }
    }

    func addVisit(_ visit: Visit) {
        visits.append(visit)
        saveData()
    }

    func deleteVisit(_ visit: Visit) {
        visits.removeAll { $0.id == visit.id }
        saveData()
    }

    func visitsForHouse(_ houseId: UUID) -> [Visit] {
        return visits.filter { $0.houseId == houseId }
    }

    // MARK: - Computed Properties

    var totalHouses: Int {
        houses.count
    }

    var newHouses: Int {
        houses.filter { $0.status == .new }.count
    }

    var activeIncidentsCount: Int {
        incidents.filter { $0.status == .active }.count
    }

    var totalRoutes: Int {
        routes.count
    }

    func activeIncidents() -> [Incident] {
        incidents.filter { $0.status == .active }
    }

    func housesByStatus(_ status: HouseStatus) -> [House] {
        houses.filter { $0.status == status }
    }

    func housesByCity(_ city: String) -> [House] {
        houses.filter { $0.city == city }
    }

    func routesForSalesperson(_ salespersonId: UUID) -> [Route] {
        routes.filter { $0.salespersonId == salespersonId }
    }

    // MARK: - Data Persistence

    private func saveData() {
        // In a real app, you'd save to Core Data or a database
        // For now, we'll use UserDefaults for demonstration
        if let housesData = try? JSONEncoder().encode(houses) {
            userDefaults.set(housesData, forKey: "houses")
        }

        if let incidentsData = try? JSONEncoder().encode(incidents) {
            userDefaults.set(incidentsData, forKey: "incidents")
        }

        if let visitsData = try? JSONEncoder().encode(visits) {
            userDefaults.set(visitsData, forKey: "visits")
        }

        if let routesData = try? JSONEncoder().encode(routes) {
            userDefaults.set(routesData, forKey: "routes")
        }
    }

    private func loadData() {
        // Load from UserDefaults
        if let housesData = userDefaults.data(forKey: "houses"),
           let decodedHouses = try? JSONDecoder().decode([House].self, from: housesData) {
            houses = decodedHouses
        }

        if let incidentsData = userDefaults.data(forKey: "incidents"),
           let decodedIncidents = try? JSONDecoder().decode([Incident].self, from: incidentsData) {
            incidents = decodedIncidents
        }

        if let visitsData = userDefaults.data(forKey: "visits"),
           let decodedVisits = try? JSONDecoder().decode([Visit].self, from: visitsData) {
            visits = decodedVisits
        }

        if let routesData = userDefaults.data(forKey: "routes"),
           let decodedRoutes = try? JSONDecoder().decode([Route].self, from: routesData) {
            routes = decodedRoutes
        }
    }

    // MARK: - Big Beautiful Program Integration

    func connectToBigBeautifulProgram() async {
        print("🔄 Attempting to connect with redundant server fallback...")

        let connected = await bigBeautifulAPIClient.connectWithFallback()

        if connected {
            print("✅ Successfully connected to Big Beautiful Program")
            await MainActor.run {
                self.isBigBeautifulConnected = true
            }

            // Load data from the connected server
            await loadContactsFromBigBeautiful()
            await loadAnalyticsFromBigBeautiful()
            await loadRollingSalesFromBigBeautiful()
            await loadIncidentsFromBigBeautiful()

            // Set sync timestamp on successful connection
            await MainActor.run {
                self.lastSyncTimestamp = Date()
            }
        } else {
            print("❌ Failed to connect to any Big Beautiful Program server")
            await MainActor.run {
                self.isBigBeautifulConnected = false
            }
        }
    }

    func loadContactsFromBigBeautiful() async {
        do {
            let response = try await bigBeautifulAPIClient.getContacts()
            await MainActor.run {
                self.contacts = response.contacts
                self.convertContactsToHouses()
            }
            print("✅ Loaded \(response.contacts.count) contacts from Big Beautiful Program")
        } catch {
            print("❌ Failed to load contacts: \(error)")
        }
    }

    func loadAnalyticsFromBigBeautiful() async {
        do {
            let analytics = try await bigBeautifulAPIClient.getAnalytics()
            await MainActor.run {
                self.analytics = analytics
            }
            print("✅ Loaded analytics from Big Beautiful Program")
        } catch {
            print("❌ Failed to load analytics: \(error)")
        }
    }

    func checkATTFiberForAddress(_ address: String) async -> FiberResponse? {
        do {
            let response = try await bigBeautifulAPIClient.checkATTFiber(address: address)
            print("✅ AT&T Fiber check for \(address): \(response.fiberAvailable)")
            return response
        } catch {
            print("❌ Failed to check AT&T Fiber: \(error)")
            return nil
        }
    }

    func geocodeAddress(_ address: String) async -> GeocodeResponse? {
        do {
            let response = try await bigBeautifulAPIClient.geocodeAddress(address: address)
            print("✅ Geocoded address: \(address) -> \(response.latitude), \(response.longitude)")
            return response
        } catch {
            print("❌ Failed to geocode address: \(error)")
            return nil
        }
    }

    func createContactInBigBeautiful(address: String, city: String, state: String, zipCode: String,
                                   ownerName: String, ownerEmail: String, ownerPhone: String, fiberAvailable: Bool) async -> Contact? {
        do {
            let contact = try await bigBeautifulAPIClient.createContact(
                address: address, city: city, state: state, zipCode: zipCode,
                ownerName: ownerName, ownerEmail: ownerEmail, ownerPhone: ownerPhone, fiberAvailable: fiberAvailable
            )
            await MainActor.run {
                self.contacts.append(contact)
            }
            print("✅ Created contact in Big Beautiful Program: \(contact.ownerName)")
            return contact
        } catch {
            print("❌ Failed to create contact: \(error)")
            return nil
        }
    }

    private func convertContactsToHouses() {
        // Convert Big Beautiful Program contacts to houses for the mobile app
        let convertedHouses = contacts.compactMap { contact -> House? in
            // Use geocoding to get coordinates if needed, for now use default coordinates
            let defaultLatitude = 34.2257 + Double.random(in: -0.1...0.1)
            let defaultLongitude = -77.9447 + Double.random(in: -0.1...0.1)

            return House(
                address: contact.address,
                city: contact.city,
                state: contact.state,
                zipCode: contact.zipCode,
                latitude: defaultLatitude,
                longitude: defaultLongitude,
                soldDate: contact.createdDate,
                price: Double(Int.random(in: 200000...400000)), // Placeholder price
                contactName: contact.ownerName,
                contactEmail: contact.ownerEmail,
                contactPhone: contact.ownerPhone,
                fiberAvailable: contact.fiberAvailable,
                adtDetected: false, // Placeholder
                adtSignDetected: Bool.random() // Placeholder for ADT sign detection
            )
        }

        // Replace sample houses with real data from Big Beautiful Program
        if !convertedHouses.isEmpty {
            houses = convertedHouses
            print("✅ Converted \(convertedHouses.count) contacts to houses")
        }
    }

    // MARK: - Additional Big Beautiful Methods

    func loadRollingSalesFromBigBeautiful() async {
        do {
            let sales = try await bigBeautifulAPIClient.getRollingSales()
            print("✅ Loaded rolling sales data from Big Beautiful Program: \(sales)")
        } catch {
            print("❌ Failed to load rolling sales: \(error)")
        }
    }

    func syncWithBigBeautiful() async {
        do {
            let result = try await bigBeautifulAPIClient.syncData()
            print("✅ Synced with Big Beautiful Program: \(result)")
            await MainActor.run {
                self.lastSyncTimestamp = Date()
            }
        } catch {
            print("❌ Failed to sync with Big Beautiful Program: \(error)")
        }
    }

    func getTerritoriesFromBigBeautiful() async -> [String: String]? {
        do {
            let territories = try await bigBeautifulAPIClient.getTerritories()
            print("✅ Loaded territories from Big Beautiful Program")
            return territories
        } catch {
            print("❌ Failed to load territories: \(error)")
            return nil
        }
    }

    func loadIncidentsFromBigBeautiful() async {
        do {
            let response = try await bigBeautifulAPIClient.getIncidents()
            await MainActor.run {
                // Convert server incidents to app incidents
                self.incidents = response.incidents.map { serverIncident in
                    Incident(
                        address: serverIncident.address,
                        incidentType: mapIncidentType(serverIncident.incident_type),
                        description: serverIncident.description,
                        latitude: serverIncident.latitude,
                        longitude: serverIncident.longitude,
                        assignedSalespersonId: salespeople.first?.id ?? UUID() // Default assignment
                    )
                }
            }
            print("✅ Loaded \(response.incidents.count) incidents from Big Beautiful Program")
        } catch {
            print("❌ Failed to load incidents: \(error)")
        }
    }
    
    private func mapIncidentType(_ serverType: String) -> IncidentType {
        switch serverType.lowercased() {
        case "fire": return .fire
        case "break_in": return .breakIn
        case "storm": return .storm
        case "flood": return .flood
        case "theft": return .theft
        default: return .theft // Default fallback
        }
    }

    func refreshBigBeautifulData() async {
        // Refresh all data from Big Beautiful Program
        await loadContactsFromBigBeautiful()
        await loadAnalyticsFromBigBeautiful()
        await loadRollingSalesFromBigBeautiful()
        await loadIncidentsFromBigBeautiful()
        await syncWithBigBeautiful()
        print("Big Beautiful Program data refreshed")
    }

    // MARK: - Region Assignment Methods

    func assignRegion(_ city: String, to salespersonId: UUID) {
        regionAssignments[city] = salespersonId
        saveRegionAssignments()
    }

    func unassignRegion(_ city: String) {
        regionAssignments.removeValue(forKey: city)
        saveRegionAssignments()
    }

    func getSalespersonForRegion(_ city: String) -> SalesPerson? {
        guard let salespersonId = regionAssignments[city] else { return nil }
        return salespeople.first { $0.id == salespersonId }
    }

    func getHousesForSalesperson(_ salespersonId: UUID) -> [House] {
        let assignedCities = regionAssignments.filter { $0.value == salespersonId }.keys
        return houses.filter { assignedCities.contains($0.city) }
    }

    func getUnassignedHouses() -> [House] {
        let assignedCities = Set(regionAssignments.keys)
        return houses.filter { !assignedCities.contains($0.city) }
    }

    func getAvailableCities() -> [String] {
        return Array(Set(houses.map { $0.city })).sorted()
    }

    func getAssignedCities() -> [String] {
        return Array(regionAssignments.keys).sorted()
    }

    private func saveRegionAssignments() {
        let assignments = Dictionary(uniqueKeysWithValues: regionAssignments.map { ($0.key, $0.value.uuidString) })
        userDefaults.set(assignments, forKey: "regionAssignments")
    }

    private func loadRegionAssignments() {
        guard let assignments = userDefaults.dictionary(forKey: "regionAssignments") as? [String: String] else { return }
        regionAssignments = assignments.compactMapValues { UUID(uuidString: $0) }
    }

    func importFromBigBeautifulProgram() {
        // This would integrate with your Big Beautiful Program
        // For now, we'll simulate importing new data

        let newHouse = House(
            address: "999 New House St",
            city: "Wilmington",
            state: "NC",
            zipCode: "28401",
            latitude: 34.2157,
            longitude: -77.9347,
            soldDate: "2024-01-20",
            price: 280000,
            contactName: "New Customer",
            contactEmail: "new@email.com",
            contactPhone: "910-555-9999",
            fiberAvailable: true,
            adtDetected: false
        )

        addHouse(newHouse)

        // Try to sync with Python backend
        syncWithBackend()
    }

    // MARK: - Backend Integration

    private func loadDataFromBackend() {
        guard let url = URL(string: "http://localhost:5001/api/houses") else { return }

        URLSession.shared.dataTask(with: url) { data, response, error in
            if let data = data {
                do {
                    let housesData = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] ?? []

                    DispatchQueue.main.async {
                        self.houses = housesData.compactMap { houseDict in
                            guard let address = houseDict["address"] as? String,
                                  let city = houseDict["city"] as? String,
                                  let state = houseDict["state"] as? String,
                                  let zipCode = houseDict["zip_code"] as? String,
                                  let latitude = houseDict["latitude"] as? Double,
                                  let longitude = houseDict["longitude"] as? Double else {
                                return nil
                            }

                            return House(
                                address: address,
                                city: city,
                                state: state,
                                zipCode: zipCode,
                                latitude: latitude,
                                longitude: longitude,
                                soldDate: "2024-01-15",
                                price: 250000,
                                contactName: "Backend Contact",
                                contactEmail: "backend@email.com",
                                contactPhone: "910-555-0000",
                                fiberAvailable: true,
                                adtDetected: false
                            )
                        }
                    }
                } catch {
                    print("Error parsing houses data: \(error)")
                }
            }
        }.resume()
    }

    private func syncWithBackend() {
        // This would sync data with your Python backend
        print("Syncing with backend...")
    }
}
