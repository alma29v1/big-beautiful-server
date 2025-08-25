import Foundation
import Combine
import CoreLocation

class DataManager: ObservableObject {
    @Published var houses: [House] = []
    @Published var routes: [Route] = []
    @Published var incidents: [Incident] = []
    @Published var contacts: [Contact] = []
    @Published var analytics: AnalyticsResponse?
    @Published var isBigBeautifulConnected = false
    @Published var lastSyncTimestamp: Date?
    @Published var regionAssignments: [String: UUID] = [:]

    let bigBeautifulAPIClient = BigBeautifulAPIClient()
    private var salesPeople: [SalesPerson] = []

    init() {
        loadRegionAssignments()
        generateSampleData()
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

            // Load real data from the connected server
            await loadContactsFromBigBeautiful()
            await loadRedfinLeadsFromBigBeautiful()
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

    func loadRedfinLeadsFromBigBeautiful() async {
        do {
            let response = try await bigBeautifulAPIClient.getRedfinLeads()
            await MainActor.run {
                self.convertRedfinLeadsToHouses(response.leads)
            }
            print("✅ Loaded \(response.leads.count) Redfin leads from Big Beautiful Program")
        } catch {
            print("❌ Failed to load Redfin leads: \(error)")
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

    func loadRollingSalesFromBigBeautiful() async {
        do {
            let rollingSales = try await bigBeautifulAPIClient.getRollingSales()
            print("✅ Loaded rolling sales data: \(rollingSales)")
        } catch {
            print("❌ Failed to load rolling sales: \(error)")
        }
    }

    func loadIncidentsFromBigBeautiful() async {
        do {
            let response = try await bigBeautifulAPIClient.getIncidents()
            await MainActor.run {
                self.incidents = response.incidents.map { serverIncident in
                    Incident(
                        id: UUID(),
                        address: serverIncident.address,
                        type: mapIncidentType(serverIncident.incident_type),
                        description: serverIncident.description,
                        date: Date(),
                        latitude: serverIncident.latitude,
                        longitude: serverIncident.longitude,
                        isActive: serverIncident.status.lowercased() == "active",
                        assignedSalesperson: serverIncident.assigned_salesperson,
                        priority: serverIncident.priority,
                        createdDate: serverIncident.created_date
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
        case "break-in", "burglary":
            return .breakIn
        case "vandalism":
            return .vandalism
        case "suspicious activity", "suspicious":
            return .suspiciousActivity
        case "theft":
            return .theft
        case "noise complaint", "noise":
            return .noiseComplaint
        default:
            return .other
        }
    }

    func syncWithBigBeautiful() async {
        await connectToBigBeautifulProgram()
    }

    func refreshBigBeautifulData() async {
        guard isBigBeautifulConnected else {
            await connectToBigBeautifulProgram()
            return
        }

        await loadContactsFromBigBeautiful()
        await loadRedfinLeadsFromBigBeautiful()
        await loadAnalyticsFromBigBeautiful()
        await loadIncidentsFromBigBeautiful()

        await MainActor.run {
            self.lastSyncTimestamp = Date()
        }
    }

    func checkATTFiberForAddress(_ address: String) async -> FiberResponse? {
        do {
            return try await bigBeautifulAPIClient.checkATTFiber(address: address)
        } catch {
            print("Failed to check ATT Fiber for \(address): \(error)")
            return nil
        }
    }

    // MARK: - Data Conversion

    private func convertContactsToHouses() {
        let newHouses = contacts.map { contact in
            House(
                id: UUID(),
                address: contact.address,
                city: contact.city,
                state: contact.state,
                zipCode: contact.zipCode,
                latitude: 0.0, // Would need geocoding
                longitude: 0.0,
                status: .available,
                ownerName: contact.ownerName,
                ownerEmail: contact.ownerEmail,
                ownerPhone: contact.ownerPhone,
                soldDate: contact.createdDate,
                price: nil,
                squareFootage: nil,
                bedrooms: nil,
                bathrooms: nil,
                adtSignDetected: false,
                notes: "Imported from \(contact.source)"
            )
        }

        // Merge with existing houses, avoiding duplicates
        for newHouse in newHouses {
            if !houses.contains(where: { $0.address == newHouse.address }) {
                houses.append(newHouse)
            }
        }
    }

    private func convertRedfinLeadsToHouses(_ leads: [RedfinLead]) {
        let newHouses = leads.map { lead in
            House(
                id: UUID(),
                address: lead.address,
                city: lead.city,
                state: lead.state,
                zipCode: lead.zipCode,
                latitude: lead.latitude,
                longitude: lead.longitude,
                status: .sold,
                ownerName: lead.ownerName,
                ownerEmail: lead.ownerEmail,
                ownerPhone: lead.ownerPhone,
                soldDate: lead.soldDate,
                price: lead.salePrice,
                squareFootage: lead.squareFeet,
                bedrooms: lead.bedrooms,
                bathrooms: lead.bathrooms,
                adtSignDetected: false,
                notes: "Redfin lead - \(lead.propertyType)"
            )
        }

        // Replace sample data with real data
        houses = newHouses
    }

    // MARK: - Region Assignment

    func assignRegion(_ region: String, to salesperson: UUID) {
        regionAssignments[region] = salesperson
        saveRegionAssignments()
    }

    func unassignRegion(_ region: String) {
        regionAssignments.removeValue(forKey: region)
        saveRegionAssignments()
    }

    func getSalespersonForRegion(_ region: String) -> SalesPerson? {
        guard let id = regionAssignments[region] else { return nil }
        return salesPeople.first { $0.id == id }
    }

    func getHousesForSalesperson(_ salesperson: SalesPerson) -> [House] {
        let assignedRegions = getAssignedCities(for: salesperson.id)
        return houses.filter { house in
            assignedRegions.contains(house.city)
        }
    }

    func getUnassignedHouses() -> [House] {
        let assignedCities = Set(regionAssignments.keys)
        return houses.filter { house in
            !assignedCities.contains(house.city)
        }
    }

    func getAvailableCities() -> [String] {
        let uniqueCities = Set(houses.map { $0.city })
        return Array(uniqueCities).sorted()
    }

    func getAssignedCities(for salespersonId: UUID) -> [String] {
        return regionAssignments.compactMap { (city, id) in
            id == salespersonId ? city : nil
        }
    }

    private func saveRegionAssignments() {
        let assignments = Dictionary(uniqueKeysWithValues: regionAssignments.map { ($0.key, $0.value.uuidString) })
        UserDefaults.standard.set(assignments, forKey: "regionAssignments")
    }

    private func loadRegionAssignments() {
        if let savedAssignments = UserDefaults.standard.dictionary(forKey: "regionAssignments") as? [String: String] {
            regionAssignments = Dictionary(uniqueKeysWithValues: savedAssignments.compactMap { (key, value) in
                guard let uuid = UUID(uuidString: value) else { return nil }
                return (key, uuid)
            })
        }
    }

    // MARK: - Sample Data Generation

    private func generateSampleData() {
        generateSampleSalespeople()
        generateSampleHouses()
        generateSampleRoutes()
        generateSampleIncidents()
    }

    private func generateSampleSalespeople() {
        salesPeople = [
            SalesPerson(id: UUID(), name: "John Smith", email: "john@company.com", phone: "555-0123", territory: "Wilmington"),
            SalesPerson(id: UUID(), name: "Sarah Johnson", email: "sarah@company.com", phone: "555-0124", territory: "Leland"),
            SalesPerson(id: UUID(), name: "Mike Davis", email: "mike@company.com", phone: "555-0125", territory: "Southport"),
            SalesPerson(id: UUID(), name: "Lisa Wilson", email: "lisa@company.com", phone: "555-0126", territory: "Hampstead")
        ]
    }

    private func generateSampleHouses() {
        houses = [
            House(
                id: UUID(),
                address: "123 Ocean View Dr",
                city: "Wilmington",
                state: "NC",
                zipCode: "28401",
                latitude: 34.2356,
                longitude: -77.9328,
                status: .available,
                ownerName: "Sample Owner 1",
                ownerEmail: "owner1@example.com",
                ownerPhone: "910-555-0201",
                soldDate: "2024-01-20",
                price: 285000,
                squareFootage: 1850,
                bedrooms: 3,
                bathrooms: 2,
                adtSignDetected: true,
                notes: "Sample data - ADT sign visible"
            ),
            House(
                id: UUID(),
                address: "456 Coastal Blvd",
                city: "Leland",
                state: "NC",
                zipCode: "28451",
                latitude: 34.2763,
                longitude: -78.0147,
                status: .sold,
                ownerName: "Sample Owner 2",
                ownerEmail: "owner2@example.com",
                ownerPhone: "910-555-0202",
                soldDate: "2024-01-21",
                price: 320000,
                squareFootage: 2200,
                bedrooms: 4,
                bathrooms: 3,
                adtSignDetected: false,
                notes: "Sample data - recently sold"
            ),
            House(
                id: UUID(),
                address: "789 Harbor Point Way",
                city: "Southport",
                state: "NC",
                zipCode: "28461",
                latitude: 33.9107,
                longitude: -78.0089,
                status: .notInterested,
                ownerName: "Sample Owner 3",
                ownerEmail: "owner3@example.com",
                ownerPhone: "910-555-0203",
                soldDate: "2024-01-22",
                price: 380000,
                squareFootage: 1950,
                bedrooms: 3,
                bathrooms: 2,
                adtSignDetected: false,
                notes: "Sample data - owner not interested"
            )
        ]
    }

    private func generateSampleRoutes() {
        routes = [
            Route(
                id: UUID(),
                name: "Morning Route - Wilmington",
                houses: Array(houses.prefix(2)),
                date: Date(),
                isCompleted: false
            ),
            Route(
                id: UUID(),
                name: "Afternoon Route - Leland",
                houses: Array(houses.suffix(1)),
                date: Date(),
                isCompleted: true
            )
        ]
    }

    private func generateSampleIncidents() {
        incidents = [
            Incident(
                id: UUID(),
                address: "789 Pine Street",
                type: .breakIn,
                description: "Forced entry through back door",
                date: Date().addingTimeInterval(-86400 * 2),
                latitude: 34.2454,
                longitude: -77.9056,
                isActive: true,
                assignedSalesperson: "John Smith",
                priority: "High",
                createdDate: "2024-01-20T10:30:00Z"
            ),
            Incident(
                id: UUID(),
                address: "456 Oak Avenue",
                type: .vandalism,
                description: "Graffiti on garage door",
                date: Date().addingTimeInterval(-86400 * 1),
                latitude: 34.2134,
                longitude: -77.8856,
                isActive: true,
                assignedSalesperson: "Sarah Johnson",
                priority: "Medium",
                createdDate: "2024-01-21T14:15:00Z"
            )
        ]
    }

    // MARK: - Data Management Methods

    func addHouse(_ house: House) {
        houses.append(house)
    }

    func updateHouse(_ house: House) {
        if let index = houses.firstIndex(where: { $0.id == house.id }) {
            houses[index] = house
        }
    }

    func deleteHouse(_ house: House) {
        houses.removeAll { $0.id == house.id }
    }

    func addRoute(_ route: Route) {
        routes.append(route)
    }

    func updateRoute(_ route: Route) {
        if let index = routes.firstIndex(where: { $0.id == route.id }) {
            routes[index] = route
        }
    }

    func deleteRoute(_ route: Route) {
        routes.removeAll { $0.id == route.id }
    }

    func getSalespeople() -> [SalesPerson] {
        return salesPeople
    }
}

extension Date {
    static func fromISO8601(_ string: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        return formatter.date(from: string)
    }
}
